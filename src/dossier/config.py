"""Run settings. Defaults live here; a TOML file can override any of them."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Effort = Literal["low", "medium", "high", "xhigh", "max"]
Role = Literal["planner", "researcher", "critic", "writer", "baseline", "judge"]


class ModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str = "claude-opus-5-5"
    effort: Effort = "medium"
    max_tokens: int = 16_000


class Models(BaseModel):
    """One model spec per role, so a cheaper worker model is a config change, not a code change."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    planner: ModelSpec = ModelSpec(effort="high")
    researcher: ModelSpec = ModelSpec(effort="medium")
    critic: ModelSpec = ModelSpec(effort="high")
    writer: ModelSpec = ModelSpec(effort="high")
    baseline: ModelSpec = ModelSpec(effort="high")
    judge: ModelSpec = ModelSpec(effort="high")

    def for_role(self, role: Role) -> ModelSpec:
        spec: ModelSpec = getattr(self, role)
        return spec


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    models: Models = Models()

    max_sub_questions: int = Field(default=4, ge=1, le=8)
    max_parallel_researchers: int = Field(default=4, ge=1)
    max_searches_per_researcher: int = Field(default=5, ge=1)
    max_research_turns: int = Field(default=8, ge=1)
    max_follow_up_rounds: int = Field(default=1, ge=0)
    researcher_timeout_s: float = Field(default=240.0, gt=0)

    budget_usd: float = Field(default=3.00, gt=0)
    # Held back from the research phase so a run that hits its budget still ends in a report.
    finish_reserve_usd: float = Field(default=0.50, ge=0)

    use_fallbacks: bool = True

    @classmethod
    def load(cls, path: Path | None) -> Settings:
        if path is None:
            return cls()
        with path.open("rb") as f:
            return cls.model_validate(tomllib.load(f))
