"""A shared spending cap for every agent in a run.

Agents run concurrently, so the check-then-spend is not atomic: several researchers can pass
the check at once and the run can overshoot by up to one call per parallel agent. That's an
accepted trade-off (a lock around the API call would serialize the team); ``finish_reserve_usd``
in :class:`~factcheck_agents.config.Settings` absorbs the overshoot.
"""

from __future__ import annotations


class BudgetExceededError(RuntimeError):
    pass


class Budget:
    def __init__(self, limit_usd: float) -> None:
        if limit_usd <= 0:
            raise ValueError("budget must be positive")
        self.limit_usd = limit_usd
        self._spent = 0.0

    @property
    def spent_usd(self) -> float:
        return self._spent

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.limit_usd - self._spent)

    def ensure(self, *, keep_in_reserve: float = 0.0) -> None:
        """Raise if starting another call would eat into ``keep_in_reserve``."""
        if self._spent >= self.limit_usd - keep_in_reserve:
            raise BudgetExceededError(
                f"spent ${self._spent:.4f} of ${self.limit_usd:.2f}"
                + (f" (${keep_in_reserve:.2f} reserved)" if keep_in_reserve else "")
            )

    def charge(self, usd: float) -> None:
        self._spent += usd
