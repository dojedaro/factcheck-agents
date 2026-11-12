"""Token accounting and cost.

Prices are USD per million tokens, first-party Claude API rates as of 2026-11. Check
https://platform.claude.com/docs/en/about-claude/pricing before trusting a bill to them.
"""

from __future__ import annotations

from dataclasses import dataclass

# model -> (input, output, cache_read) per 1M tokens. Cache writes bill at 1.25x input.
PRICES: dict[str, tuple[float, float, float]] = {
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
    "claude-opus-5": (5.00, 25.00, 0.50),
    "claude-opus-4-8": (5.00, 25.00, 0.50),
    "claude-sonnet-5": (2.00, 10.00, 0.20),
}
CACHE_WRITE_MULTIPLIER = 1.25
WEB_SEARCH_USD = 10.00 / 1000  # per search
# Unknown models are billed at the most expensive known rate so budgets fail safe.
_FALLBACK_PRICE = max(PRICES.values())


@dataclass(frozen=True, slots=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    web_searches: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cache_read_tokens + other.cache_read_tokens,
            self.cache_write_tokens + other.cache_write_tokens,
            self.web_searches + other.web_searches,
        )


def is_priced(model: str) -> bool:
    return model in PRICES


def cost_usd(model: str, usage: TokenUsage) -> float:
    inp, out, cache_read = PRICES.get(model, _FALLBACK_PRICE)
    tokens = (
        usage.input_tokens * inp
        + usage.output_tokens * out
        + usage.cache_read_tokens * cache_read
        + usage.cache_write_tokens * inp * CACHE_WRITE_MULTIPLIER
    )
    return tokens / 1_000_000 + usage.web_searches * WEB_SEARCH_USD
