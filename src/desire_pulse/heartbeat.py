"""Heartbeat scheduling, election, repeat control, and failure recovery."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .models import HeartbeatConfig, HeartbeatDecision, Snapshot


ACTION_FOR_MOTIVE = {
    "attachment": "reach_partner",
    "curiosity": "explore",
    "reflection": "reflect",
    "duty": "create",
    "social": "socialize",
    "libido": "private_reverie",
    "stress": "rest",
}


class HeartbeatController:
    def __init__(self, config: HeartbeatConfig | None = None, *, timezone: str = "UTC", seed: str = "public-example"):
        self.config = config or HeartbeatConfig()
        self.timezone = timezone
        self.seed = seed
        if self.config.min_interval_seconds <= 0 or self.config.max_interval_seconds < self.config.min_interval_seconds:
            raise ValueError("invalid heartbeat interval")

    def new_state(self) -> dict:
        return {
            "version": 1,
            "day": "",
            "wake_count": 0,
            "next_wake_at": 0.0,
            "last_action": "none",
            "last_motive": "none",
            "skipped_until": {},
            "consecutive_failures": 0,
            "halted": False,
            "last_result": "never",
            "activity_history": [],
            "processed_decision_ids": [],
        }

    def schedule_next(self, state: dict, now: float | None = None) -> float:
        now = time.time() if now is None else float(now)
        bucket = int(now // 60)
        digest = hashlib.sha256(f"{self.seed}:wake:{bucket}".encode()).digest()
        unit = int.from_bytes(digest[:8], "big") / 2**64
        span = self.config.max_interval_seconds - self.config.min_interval_seconds
        state["next_wake_at"] = now + self.config.min_interval_seconds + int(unit * span)
        return state["next_wake_at"]

    def elect(self, state: dict, snapshot: Snapshot, now: float | None = None) -> HeartbeatDecision:
        now = time.time() if now is None else float(now)
        self._roll_day(state, now)
        if state.get("halted"):
            return self._decision(state, now, "none", "recovery", False, "circuit breaker is open")
        if state["wake_count"] >= self.config.daily_limit:
            return self._decision(state, now, "none", "daily_limit", False, "daily wake limit reached")
        if self._quiet(now):
            return self._decision(state, now, "rest", "quiet_hours", False, "inside quiet hours")

        scores = dict(snapshot.drives)
        scores.pop("fatigue", None)
        previous = state.get("last_motive")
        if previous in scores:
            scores[previous] = max(0.0, scores[previous] - self.config.repeat_penalty)
        motive = max(scores, key=scores.get)
        action = ACTION_FOR_MOTIVE.get(motive, "rest")
        if float(state.get("skipped_until", {}).get(action, 0.0)) > now:
            alternatives = {key: value for key, value in scores.items() if ACTION_FOR_MOTIVE.get(key) != action}
            motive = max(alternatives, key=alternatives.get) if alternatives else "stress"
            action = ACTION_FOR_MOTIVE.get(motive, "rest")

        should_contact = action == "reach_partner"
        state["wake_count"] += 1
        state["last_action"] = action
        state["last_motive"] = motive
        return self._decision(state, now, action, motive, should_contact, "highest eligible drive after penalties")

    def record_result(self, state: dict, status: str, now: float | None = None, *, action: str | None = None, decision_id: str | None = None) -> None:
        now = time.time() if now is None else float(now)
        action = action or state.get("last_action", "none")
        if decision_id and decision_id in state.setdefault("processed_decision_ids", []):
            return
        state["last_result"] = status
        if status == "failed":
            state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1
            failures = state["consecutive_failures"]
            index = min(failures - 1, len(self.config.failure_backoff_seconds) - 1)
            state["next_wake_at"] = now + self.config.failure_backoff_seconds[index]
            if failures >= self.config.circuit_breaker_failures:
                state["halted"] = True
        else:
            state["consecutive_failures"] = 0
            if status == "skipped" and action != "none":
                state.setdefault("skipped_until", {})[action] = now + self.config.skip_cooldown_seconds
            self.schedule_next(state, now)
        state.setdefault("activity_history", []).append({
            "decision_id": decision_id or "untracked",
            "at": now,
            "action": action,
            "status": status,
        })
        state["activity_history"] = state["activity_history"][-128:]
        if decision_id:
            state["processed_decision_ids"].append(decision_id)
            state["processed_decision_ids"] = state["processed_decision_ids"][-256:]

    def recover(self, state: dict, now: float | None = None) -> None:
        now = time.time() if now is None else float(now)
        state["halted"] = False
        state["consecutive_failures"] = 0
        state["last_result"] = "manually_recovered"
        self.schedule_next(state, now)

    def _decision(self, state: dict, now: float, action: str, motive: str, contact: bool, reason: str) -> HeartbeatDecision:
        next_at = state.get("next_wake_at") or self.schedule_next(state, now)
        decision_id = hashlib.sha256(f"{self.seed}:{now:.6f}:{action}:{motive}".encode()).hexdigest()[:20]
        return HeartbeatDecision(decision_id, now, action, motive, contact, reason, float(next_at))

    def _roll_day(self, state: dict, now: float) -> None:
        day = datetime.fromtimestamp(now, ZoneInfo(self.timezone)).date().isoformat()
        if state.get("day") != day:
            state["day"] = day
            state["wake_count"] = 0

    def _quiet(self, now: float) -> bool:
        hour = datetime.fromtimestamp(now, ZoneInfo(self.timezone)).hour
        start, end = self.config.quiet_start_hour, self.config.quiet_end_hour
        return start <= hour < end if start <= end else hour >= start or hour < end
