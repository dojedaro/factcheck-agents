import pytest

from dossier.config import Settings
from dossier.evaluation import run_eval, verdict_from_swapped
from dossier.llm.fake import FakeLLM
from dossier.schemas import Judgment


def j(winner: str) -> Judgment:
    return Judgment(winner=winner, reasoning="")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ("A", "B", "team"),  # team won in both positions
        ("B", "A", "baseline"),
        ("A", "A", "tie"),  # judge just prefers position A: bias, not quality
        ("tie", "B", "tie"),
    ],
)
def test_a_side_only_wins_if_it_wins_in_both_orders(first, second, expected):
    assert verdict_from_swapped(j(first), j(second)) == expected


async def test_eval_writes_artifacts_and_cancels_position_bias(tmp_path):
    summary = await run_eval(FakeLLM(), Settings(), ["Q one?", "Q two?"], tmp_path)

    # FakeLLM's judge always picks position A, so every swapped pair must come out a tie.
    assert "2 questions, 2 ties" in summary
    assert (tmp_path / "results.jsonl").read_text().count("\n") == 2
    assert (tmp_path / "q01-team.md").exists()
    assert (tmp_path / "q02-baseline.trace.jsonl").exists()


def test_dotenv_loads_keys_without_overriding_real_env(tmp_path, monkeypatch):
    from dossier.cli import load_dotenv

    env = tmp_path / ".env"
    env.write_text('# comment\nDOSSIER_A="from file"\nDOSSIER_B=from file\n', encoding="utf-8")
    monkeypatch.delenv("DOSSIER_A", raising=False)
    monkeypatch.setenv("DOSSIER_B", "real")

    load_dotenv(env)

    import os

    assert os.environ["DOSSIER_A"] == "from file"
    assert os.environ["DOSSIER_B"] == "real"
