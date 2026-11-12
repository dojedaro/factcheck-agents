"""The real client's tool loop, against a stubbed SDK. No network, no key.

The responses are real ``BetaMessage`` objects built from API-shaped dicts, so these tests
catch drift between our parsing and the SDK's types."""

from typing import Any

import pytest
from anthropic.types.beta import BetaMessage

from dossier.config import ModelSpec
from dossier.llm.anthropic_llm import FALLBACK_BETA, AnthropicLLM
from dossier.llm.base import LLMError, RefusalError
from dossier.schemas import ResearchNotes

SPEC = ModelSpec()
VALID_NOTES = {
    "summary": "s",
    "findings": [{"claim": "c", "source_url": "https://a.com/x", "quote": "q"}],
    "open_gaps": [],
}


def msg(stop_reason: str, *content: dict[str, Any], model: str = "claude-opus-5-5", searches: int = 0):
    return BetaMessage.model_validate(
        {
            "id": "msg_x",
            "type": "message",
            "role": "assistant",
            "model": model,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "content": list(content),
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "server_tool_use": {"web_search_requests": searches, "web_fetch_requests": 0},
            },
        }
    )


def search_result(url: str, title: str = "T") -> dict[str, Any]:
    return {
        "type": "web_search_tool_result",
        "tool_use_id": "srvtoolu_1",
        "content": [{"type": "web_search_result", "url": url, "title": title, "encrypted_content": "e"}],
    }


def submit(payload: dict[str, Any], tool_id: str = "toolu_1") -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": "submit", "input": payload}


def text(t: str) -> dict[str, Any]:
    return {"type": "text", "text": t}


class StubMessages:
    def __init__(self, responses: list[BetaMessage]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> BetaMessage:
        # Snapshot: the loop mutates its messages list after each call.
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


class StubClient:
    def __init__(self, responses: list[BetaMessage]) -> None:
        self.beta = type("Beta", (), {})()
        self.beta.messages = StubMessages(responses)


def llm_with(*responses: BetaMessage, **kwargs: Any) -> tuple[AnthropicLLM, StubMessages]:
    client = StubClient(list(responses))
    return AnthropicLLM(client, **kwargs), client.beta.messages  # type: ignore[arg-type]


async def research(llm: AnthropicLLM):
    return await llm.research(SPEC, system="s", prompt="p", schema=ResearchNotes, max_searches=3, max_turns=5)


async def test_collects_sources_and_returns_validated_submission():
    llm, stub = llm_with(
        msg("tool_use", search_result("https://a.com/x", "A"), submit(VALID_NOTES), searches=1),
    )
    result = await research(llm)

    assert result.output.findings[0].source_url == "https://a.com/x"
    assert [s.title for s in result.sources] == ["A"]
    assert result.usage.web_searches == 1
    req = stub.requests[0]
    assert req["fallbacks"] == "default" and req["betas"] == [FALLBACK_BETA]
    assert req["output_config"] == {"effort": SPEC.effort}
    assert req["cache_control"] == {"type": "ephemeral"}  # the loop resends history every turn
    assert {t["name"] for t in req["tools"]} == {"web_search", "submit"}
    assert next(t for t in req["tools"] if t["name"] == "submit")["strict"] is True


async def test_resumes_after_pause_turn_and_keeps_sources_from_every_turn():
    llm, stub = llm_with(
        msg("pause_turn", search_result("https://a.com/x")),
        msg("tool_use", search_result("https://b.com/y"), submit(VALID_NOTES)),
    )
    result = await research(llm)

    assert {s.url for s in result.sources} == {"https://a.com/x", "https://b.com/y"}
    # Resume = resend with the paused assistant turn appended, no new user turn.
    assert [m["role"] for m in stub.requests[1]["messages"]] == ["user", "assistant"]


async def test_invalid_submission_gets_an_error_tool_result_then_retries():
    llm, stub = llm_with(
        msg("tool_use", submit({"summary": "missing fields"}, "toolu_bad")),
        msg("tool_use", submit(VALID_NOTES, "toolu_good")),
    )
    await research(llm)

    error_turn = stub.requests[1]["messages"][-1]
    block = error_turn["content"][0]
    assert block["type"] == "tool_result" and block["tool_use_id"] == "toolu_bad" and block["is_error"]


async def test_nudges_once_if_the_model_stops_without_submitting():
    llm, stub = llm_with(msg("end_turn", text("done")), msg("tool_use", submit(VALID_NOTES)))
    await research(llm)
    assert "submit" in stub.requests[1]["messages"][-1]["content"]


async def test_gives_up_after_a_second_stop_without_submitting():
    llm, _ = llm_with(msg("end_turn", text("done")), msg("end_turn", text("still done")))
    with pytest.raises(LLMError, match="no valid `submit`"):
        await research(llm)


async def test_refusal_raises_a_typed_error():
    llm, _ = llm_with(msg("refusal"))
    with pytest.raises(RefusalError):
        await research(llm)


async def test_reports_the_model_that_actually_served_the_request():
    llm, _ = llm_with(msg("tool_use", submit(VALID_NOTES), model="claude-opus-4-8"))
    assert (await research(llm)).model == "claude-opus-4-8"


async def test_fallbacks_can_be_turned_off():
    llm, stub = llm_with(msg("tool_use", submit(VALID_NOTES)), use_fallbacks=False)
    await research(llm)
    assert "fallbacks" not in stub.requests[0] and "betas" not in stub.requests[0]
