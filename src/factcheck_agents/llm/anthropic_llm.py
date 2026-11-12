"""The real model: Claude through the official Anthropic SDK.

Design notes, so the choices are defensible:

* Beta namespace throughout, for server-side refusal fallbacks (``fallbacks="default"``):
  if a safety classifier declines, the API re-runs the request on a fallback model inside
  the same call instead of failing the agent.
* Structured outputs (``messages.parse``) for single-shot agents; the response is validated
  against the Pydantic model by the SDK.
* Researchers can't use structured outputs alongside an open-ended search loop, so they end
  by calling a strict ``submit`` tool whose schema is the Pydantic model. Forced
  ``tool_choice`` is rejected on current models, so the prompt asks for the call and the loop
  nudges once if the model stops without making it.
* Thinking is left at the model default (adaptive); ``effort`` is the depth control.
* The research loop is append-only (assistant turns are replayed unchanged, nudges are new
  turns), which keeps both the prompt cache and replayed thinking blocks valid.
* Retries for 429/5xx/connection errors are the SDK's own (exponential backoff).
"""

from __future__ import annotations

from typing import Any, cast

from anthropic import AsyncAnthropic, transform_schema
from anthropic.types.beta import BetaMessage, BetaMessageParam, BetaToolResultBlockParam
from pydantic import ValidationError

from factcheck_agents.config import ModelSpec
from factcheck_agents.llm.base import Completion, LLMError, RefusalError, T, TruncatedError
from factcheck_agents.pricing import TokenUsage
from factcheck_agents.schemas import Source

FALLBACK_BETA = "server-side-fallback-2026-07-01"
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-2"}
SUBMIT_TOOL = "submit"
_NUDGE = f"You stopped without calling `{SUBMIT_TOOL}`. Call it now with your findings."


class AnthropicLLM:
    def __init__(self, client: AsyncAnthropic | None = None, *, use_fallbacks: bool = True) -> None:
        self._client = client or AsyncAnthropic(max_retries=4)
        self._use_fallbacks = use_fallbacks

    # ------------------------------------------------------------------ public API

    async def structured(
        self, spec: ModelSpec, *, system: str, prompt: str, schema: type[T]
    ) -> Completion[T]:
        resp = await self._client.beta.messages.parse(
            **self._request_options(spec),
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
        )
        _raise_for_stop(resp)
        if resp.parsed_output is None:
            raise LLMError(f"no parsable {schema.__name__} in response {_request_id(resp)}")
        return Completion(resp.parsed_output, resp.model, _usage(resp), request_ids=[_request_id(resp)])

    async def research(
        self,
        spec: ModelSpec,
        *,
        system: str,
        prompt: str,
        schema: type[T],
        max_searches: int,
        max_turns: int,
    ) -> Completion[T]:
        tools: list[Any] = [
            {"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches},
            {
                "name": SUBMIT_TOOL,
                "description": "Submit your final result. Call exactly once, when research is done.",
                "input_schema": transform_schema(schema),
                "strict": True,
            },
        ]
        messages: list[BetaMessageParam] = [{"role": "user", "content": prompt}]
        usage, sources, request_ids = TokenUsage(), _SourceLog(), []
        nudged = False

        for _ in range(max_turns):
            resp = await self._client.beta.messages.create(
                **self._request_options(spec),
                system=system,
                messages=messages,
                tools=tools,
                # Each turn resends the whole conversation, search results included. Automatic
                # caching moves the breakpoint forward every turn, so earlier turns bill as cache
                # reads (0.05x input on Opus 5.5) instead of full-price input.
                cache_control={"type": "ephemeral"},
            )
            usage += _usage(resp)
            request_ids.append(_request_id(resp))
            sources.collect(resp)
            _raise_for_stop(resp)
            # Append the assistant turn unchanged: thinking blocks must be replayed as-is.
            messages.append({"role": "assistant", "content": cast(Any, resp.content)})

            if resp.stop_reason == "pause_turn":  # server tool loop hit its turn limit; resume
                continue

            submit = next((b for b in resp.content if b.type == "tool_use" and b.name == SUBMIT_TOOL), None)
            if submit is not None:
                try:
                    output = schema.model_validate(submit.input)
                except ValidationError as exc:
                    messages.append(_tool_error(submit.id, f"Invalid submission, fix and resubmit: {exc}"))
                    continue
                return Completion(output, resp.model, usage, sources.items, request_ids)

            if nudged:
                break
            messages.append({"role": "user", "content": _NUDGE})
            nudged = True

        raise LLMError(f"no valid `{SUBMIT_TOOL}` call after {max_turns} turns (requests {request_ids})")

    # ------------------------------------------------------------------ helpers

    def _request_options(self, spec: ModelSpec) -> dict[str, Any]:
        options: dict[str, Any] = {
            "model": spec.model,
            "max_tokens": spec.max_tokens,
            "output_config": {"effort": spec.effort},
        }
        if self._use_fallbacks and spec.model in _FALLBACK_MODELS:
            options["betas"] = [FALLBACK_BETA]
            options["fallbacks"] = "default"
        return options


class _SourceLog:
    """Every page web_search returned, deduplicated by URL, in the order first seen."""

    def __init__(self) -> None:
        self._by_url: dict[str, Source] = {}

    @property
    def items(self) -> list[Source]:
        return list(self._by_url.values())

    def collect(self, resp: BetaMessage) -> None:
        for block in resp.content:
            if block.type != "web_search_tool_result":
                continue
            if not isinstance(block.content, list):  # an error object, not results
                continue
            for result in block.content:
                self._by_url.setdefault(result.url, Source(result.url, result.title, result.page_age))


def _raise_for_stop(resp: BetaMessage) -> None:
    if resp.stop_reason == "refusal":
        details = resp.stop_details
        raise RefusalError(f"model declined ({details.category if details else 'unknown'})")
    if resp.stop_reason == "max_tokens":
        raise TruncatedError(f"hit max_tokens on request {_request_id(resp)}")


def _usage(resp: BetaMessage) -> TokenUsage:
    u = resp.usage
    return TokenUsage(
        input_tokens=u.input_tokens,
        output_tokens=u.output_tokens,
        cache_read_tokens=u.cache_read_input_tokens or 0,
        cache_write_tokens=u.cache_creation_input_tokens or 0,
        web_searches=u.server_tool_use.web_search_requests if u.server_tool_use else 0,
    )


def _tool_error(tool_use_id: str, message: str) -> BetaMessageParam:
    result: BetaToolResultBlockParam = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": message,
        "is_error": True,
    }
    return {"role": "user", "content": [result]}


def _request_id(resp: BetaMessage) -> str:
    # Set by the SDK from the `request-id` header; log it when reporting a failure to Anthropic.
    return getattr(resp, "_request_id", None) or ""


__all__ = ["AnthropicLLM"]
