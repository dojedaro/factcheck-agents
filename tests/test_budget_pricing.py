import pytest

from factcheck_agents.budget import Budget, BudgetExceededError
from factcheck_agents.pricing import TokenUsage, cost_usd


def test_cost_matches_published_rates():
    usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000, web_searches=100)
    assert cost_usd("claude-opus-5-5", usage) == pytest.approx(4 + 20 + 1)


def test_cache_tokens_are_priced_separately():
    usage = TokenUsage(cache_read_tokens=1_000_000, cache_write_tokens=1_000_000)
    assert cost_usd("claude-opus-5-5", usage) == pytest.approx(0.20 + 4 * 1.25)


def test_unknown_model_is_billed_at_the_highest_rate():
    usage = TokenUsage(input_tokens=1_000_000)
    assert cost_usd("some-future-model", usage) >= cost_usd("claude-opus-5-5", usage)


def test_usage_adds_up():
    total = TokenUsage(1, 2, 3, 4, 5) + TokenUsage(10, 20, 30, 40, 50)
    assert total == TokenUsage(11, 22, 33, 44, 55)


def test_budget_respects_reserve():
    budget = Budget(1.0)
    budget.charge(0.7)
    budget.ensure()  # 0.3 left, no reserve needed
    with pytest.raises(BudgetExceededError, match="reserved"):
        budget.ensure(keep_in_reserve=0.4)
    assert budget.remaining_usd == pytest.approx(0.3)


def test_budget_rejects_nonsense_limit():
    with pytest.raises(ValueError):
        Budget(0)
