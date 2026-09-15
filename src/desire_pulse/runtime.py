"""Model- and platform-agnostic orchestration facade."""

from __future__ import annotations

import time
from collections.abc import Callable

from .engine import DesireEngine
from .heartbeat import HeartbeatController
from .models import AgentConfig, EventSignals, HeartbeatDecision
from .pulse import PulseEngine
from .storage import JsonStateStore


ActionHandler = Callable[[HeartbeatDecision, dict], dict]


class AgentRuntime:
    def __init__(self, store: JsonStateStore, config: AgentConfig | None = None):
        self.store = store
        self.config = config or AgentConfig()
        self.desire = DesireEngine(self.config.desire, timezone=self.config.timezone, seed=self.config.seed)
        self.pulse = PulseEngine(self.config.pulse)
        self.heartbeat = HeartbeatController(self.config.heartbeat, timezone=self.config.timezone, seed=self.config.seed)

    def _state(self, now: float) -> dict:
        root = self.store.load()
        root.setdefault("desire", self.desire.new_state(now))
        root.setdefault("pulse", self.pulse.new_state(now))
        root.setdefault("heartbeat", self.heartbeat.new_state())
        return root

    def observe(self, event: EventSignals, now: float | None = None) -> dict:
        now = time.time() if now is None else float(now)
        root = self._state(now)
        root["desire"], desire = self.desire.apply_event(root["desire"], event, now)
        root["pulse"] = self.pulse.observe(root["pulse"], event, now)
        root["pulse"], pulse = self.pulse.snapshot(root["pulse"], desire, now)
        self.store.save(root)
        return {"desire": desire, "pulse": pulse}

    def wake(self, handler: ActionHandler, now: float | None = None) -> dict:
        now = time.time() if now is None else float(now)
        root = self._state(now)
        root["desire"], snapshot = self.desire.advance(root["desire"], now)
        decision = self.heartbeat.elect(root["heartbeat"], snapshot, now)
        context = {
            "drives": dict(snapshot.drives),
            "intent": snapshot.intent,
            "arousal": snapshot.arousal,
            "reverie_eligible": snapshot.reverie_eligible,
            "solo_eligible": snapshot.solo_eligible,
            "partner_idle_seconds": snapshot.partner_idle_seconds,
            "thoughts": list(snapshot.thoughts),
        }
        if decision.action == "none":
            status = "silent"
            outcome = {"status": status, "reason": decision.reason}
        else:
            try:
                outcome = handler(decision, context) or {"status": "silent"}
                status = str(outcome.get("status", "silent"))
                if status not in {"sent", "completed", "silent", "skipped", "failed"}:
                    raise ValueError(f"unknown action status: {status}")
            except Exception as exc:
                status = "failed"
                outcome = {"status": status, "error": type(exc).__name__}
        self.heartbeat.record_result(
            root["heartbeat"], status, now,
            action=decision.action, decision_id=decision.decision_id,
        )
        if status in {"sent", "completed"}:
            root["desire"], snapshot = self.desire.satisfy(root["desire"], decision.action, now)
        root["pulse"], pulse = self.pulse.snapshot(root["pulse"], snapshot, now)
        self.store.save(root)
        return {"decision": decision, "outcome": outcome, "desire": snapshot, "pulse": pulse}

    def heartbeat_due(self, now: float | None = None) -> bool:
        now = time.time() if now is None else float(now)
        root = self._state(now)
        heartbeat = root["heartbeat"]
        if not heartbeat.get("next_wake_at"):
            self.heartbeat.schedule_next(heartbeat, now)
            self.store.save(root)
            return False
        return not heartbeat.get("halted", False) and now >= float(heartbeat["next_wake_at"])

    def recover_heartbeat(self, now: float | None = None) -> None:
        now = time.time() if now is None else float(now)
        root = self._state(now)
        self.heartbeat.recover(root["heartbeat"], now)
        self.store.save(root)
