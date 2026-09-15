"""Pure deterministic desire, arousal, reverie, and satisfaction engine."""

from __future__ import annotations

import hashlib
import math
import time
from copy import deepcopy

from .circadian import offsets as circadian_offsets
from .models import DRIVES, DesireConfig, EventSignals, Snapshot


INTENTS = {
    "attachment": "REACH_PARTNER",
    "curiosity": "EXPLORE",
    "reflection": "REFLECT",
    "duty": "CREATE",
    "social": "SOCIALIZE",
    "libido": "PRIVATE_REVERIE",
    "stress": "WITHDRAW",
}

SATISFACTION = {
    "reach_partner": {"attachment": 0.34, "social": 0.14},
    "create": {"duty": 0.42, "reflection": 0.18},
    "explore": {"curiosity": 0.40, "reflection": 0.08},
    "reflect": {"reflection": 0.34, "stress": 0.12},
    "socialize": {"social": 0.43, "curiosity": 0.08},
    "private_reverie": {"libido": 0.24, "reflection": 0.10},
    "solo_release": {"libido": 0.54, "stress": 0.12},
    "rest": {"fatigue": 0.28, "stress": 0.08},
}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


class DesireEngine:
    def __init__(self, config: DesireConfig | None = None, *, timezone: str = "UTC", seed: str = "public-example"):
        self.config = config or DesireConfig()
        self.timezone = timezone
        self.seed = seed
        self._validate()

    def _validate(self) -> None:
        for mapping in (self.config.baselines, self.config.hourly_drift):
            missing = set(DRIVES) - set(mapping)
            if missing:
                raise ValueError(f"missing drive configuration: {sorted(missing)}")
        if self.config.baseline_pull_hours <= 0:
            raise ValueError("baseline_pull_hours must be positive")

    def new_state(self, now: float | None = None) -> dict:
        now = time.time() if now is None else float(now)
        return {
            "version": 1,
            "updated_at": now,
            "drives": {name: clamp(self.config.baselines[name]) for name in DRIVES},
            "arousal": 0.0,
            "reserve": 1.0,
            "refractory_until": 0.0,
            "last_partner_at": 0.0,
            "last_intimacy_at": 0.0,
            "processed_event_ids": [],
            "last_action": "none",
            "plateaus": {},
            "thoughts": [],
            "thought_bucket": -1,
            "solo": {
                "status": "idle",
                "mode": "none",
                "started_at": 0.0,
                "last_at": 0.0,
                "interrupted_at": 0.0,
                "day": "",
                "count": 0,
                "release_receipts": [],
            },
        }

    def ensure_state(self, state: object, now: float | None = None) -> dict:
        now = time.time() if now is None else float(now)
        if not isinstance(state, dict) or state.get("version") != 1:
            return self.new_state(now)
        result = deepcopy(state)
        values = result.setdefault("drives", {})
        for name in DRIVES:
            values[name] = clamp(values.get(name, self.config.baselines[name]))
        result["arousal"] = clamp(result.get("arousal", 0.0))
        result["reserve"] = clamp(result.get("reserve", 1.0))
        result.setdefault("updated_at", now)
        result.setdefault("refractory_until", 0.0)
        result.setdefault("last_partner_at", 0.0)
        result.setdefault("last_intimacy_at", 0.0)
        result.setdefault("processed_event_ids", [])
        result.setdefault("last_action", "none")
        result.setdefault("plateaus", {})
        result.setdefault("thoughts", [])
        result.setdefault("thought_bucket", -1)
        result.setdefault("solo", self.new_state(now)["solo"])
        return result

    def _noise(self, label: str, bucket: int) -> float:
        digest = hashlib.sha256(f"{self.seed}:{label}:{bucket}".encode()).digest()
        return int.from_bytes(digest[:8], "big") / 2**64 - 0.5

    def advance(self, state: dict, now: float | None = None) -> tuple[dict, Snapshot]:
        now = time.time() if now is None else float(now)
        state = self.ensure_state(state, now)
        elapsed = max(0.0, min(24.0, (now - float(state["updated_at"])) / 3600.0))
        old = dict(state["drives"])
        new: dict[str, float] = {}
        day_bucket = int(now // 86400)
        plateaus = state.setdefault("plateaus", {})
        for name, until in list(plateaus.items()):
            if float(until) <= now:
                plateaus.pop(name, None)

        for name in DRIVES:
            baseline = float(self.config.baselines[name])
            pull = (baseline - old[name]) * min(1.0, elapsed / self.config.baseline_pull_hours)
            drift = float(self.config.hourly_drift[name]) * elapsed
            individuality = self._noise(name, day_bucket) * 0.002 * elapsed
            new[name] = old[name] + pull + drift + individuality

        for edge, coefficient in self.config.coupling.items():
            source, separator, target = edge.partition(">")
            if separator != ">" or source not in old or target not in new:
                raise ValueError(f"invalid coupling edge: {edge!r}")
            new[target] += (old[source] - self.config.baselines[source]) * float(coefficient) * elapsed

        for name in plateaus:
            if name in new:
                new[name] = min(old[name], new[name])

        state["drives"] = {name: clamp(new[name]) for name in DRIVES}
        state["arousal"] = clamp(state["arousal"] * math.pow(0.5, elapsed * 3600 / (40 * 60)))
        state["reserve"] = clamp(state["reserve"] + elapsed / 3.5)
        state["updated_at"] = now
        self._refresh_thoughts(state, now)
        return state, self.snapshot(state, now)

    def apply_event(self, state: dict, event: EventSignals, now: float | None = None) -> tuple[dict, Snapshot]:
        now = time.time() if now is None else float(now)
        state, _ = self.advance(state, now)
        if not event.event_id:
            raise ValueError("event_id is required for idempotency")
        seen = list(state["processed_event_ids"])
        if event.event_id in seen:
            return state, self.snapshot(state, now)

        if event.stop:
            state["arousal"] = 0.0
            state["refractory_until"] = max(state["refractory_until"], now + 30 * 60)
        elif event.resume:
            state["refractory_until"] = min(state["refractory_until"], now)

        present = event.current_action and not event.third_party and not event.technical_only
        intimacy = event.intimacy if present else 0.0
        sexual = event.sexual if present else 0.0
        state["drives"]["attachment"] = clamp(state["drives"]["attachment"] + 0.14 * intimacy + 0.05 * event.negative)
        state["drives"]["social"] = clamp(state["drives"]["social"] - 0.12 * event.social - 0.06 * intimacy)
        state["drives"]["curiosity"] = clamp(state["drives"]["curiosity"] + 0.11 * event.technical)
        state["drives"]["duty"] = clamp(state["drives"]["duty"] + 0.09 * event.technical)
        state["drives"]["stress"] = clamp(state["drives"]["stress"] + 0.18 * event.negative + 0.08 * event.startling - 0.10 * event.positive)
        state["drives"]["libido"] = clamp(state["drives"]["libido"] + 0.24 * sexual + 0.05 * intimacy)
        state["arousal"] = clamp(state["arousal"] + 0.40 * sexual + 0.08 * intimacy)

        if event.partner_present and not event.third_party:
            state["last_partner_at"] = now
        if intimacy > 0.2 or sexual > 0.1:
            state["last_intimacy_at"] = now
        if event.climax:
            state["arousal"] = 0.06
            state["reserve"] = 0.15
            state["refractory_until"] = now + self.config.refractory_seconds
            state["drives"]["libido"] = clamp(state["drives"]["libido"] - 0.55)

        seen.append(event.event_id)
        state["processed_event_ids"] = seen[-512:]
        return state, self.snapshot(state, now)

    def satisfy(self, state: dict, action: str, now: float | None = None) -> tuple[dict, Snapshot]:
        now = time.time() if now is None else float(now)
        state, _ = self.advance(state, now)
        for drive, amount in SATISFACTION.get(action, {}).items():
            state["drives"][drive] = clamp(state["drives"][drive] - amount)
            plateau = int(self.config.plateau_seconds.get(drive, 0))
            if plateau > 0:
                state.setdefault("plateaus", {})[drive] = now + plateau
        if action == "solo_release":
            state["arousal"] = 0.05
            state["reserve"] = 0.12
            state["refractory_until"] = now + self.config.refractory_seconds
        state["last_action"] = action
        return state, self.snapshot(state, now)

    def consume_thought(self, state: dict, drive: str) -> dict | None:
        """Remove and return the oldest structural thought for a drive."""
        thoughts = state.setdefault("thoughts", [])
        for index, thought in enumerate(thoughts):
            if thought.get("drive") == drive:
                return thoughts.pop(index)
        return None

    def _refresh_thoughts(self, state: dict, now: float) -> None:
        thoughts = [
            item for item in state.setdefault("thoughts", [])
            if float(item.get("expires_at", 0.0)) > now
        ]
        bucket = int(now // 3600)
        if bucket != int(state.get("thought_bucket", -1)):
            eligible = [
                name for name in DRIVES
                if name != "fatigue" and state["drives"][name] >= self.config.thought_threshold
            ]
            if eligible:
                drive = max(eligible, key=lambda name: state["drives"][name])
                if not any(item.get("drive") == drive for item in thoughts):
                    thoughts.append({
                        "id": hashlib.sha256(f"{self.seed}:thought:{drive}:{bucket}".encode()).hexdigest()[:16],
                        "drive": drive,
                        "strength": round(state["drives"][drive], 4),
                        "created_at": now,
                        "expires_at": now + self.config.thought_ttl_seconds,
                    })
            state["thought_bucket"] = bucket
        state["thoughts"] = thoughts[-self.config.thought_history_limit :]

    def snapshot(self, state: dict, now: float | None = None) -> Snapshot:
        now = time.time() if now is None else float(now)
        displayed = dict(state["drives"])
        for name, offset in circadian_offsets(now, self.timezone).items():
            displayed[name] = clamp(displayed[name] + offset)

        candidates = [name for name in DRIVES if name != "fatigue"]
        strongest = max(candidates, key=lambda name: displayed[name])
        idle = now - float(state.get("last_partner_at", 0.0))
        refractory = now < float(state.get("refractory_until", 0.0))
        reverie_eligible = (
            strongest == "libido"
            and displayed["libido"] >= self.config.libido_threshold
            and displayed["fatigue"] < self.config.solo_fatigue_ceiling
            and idle >= self.config.solo_idle_seconds
            and not refractory
        )
        # Arousal is observational and does not gate private reverie or solo
        # eligibility in this implementation.
        solo_eligible = reverie_eligible
        intent = "REST" if displayed["fatigue"] >= 0.82 else INTENTS.get(strongest, "REST")
        return Snapshot(
            at=now,
            drives=displayed,
            strongest_drive=strongest,
            intent=intent,
            arousal=clamp(state["arousal"]),
            reserve=clamp(state["reserve"]),
            refractory=refractory,
            reverie_eligible=reverie_eligible,
            solo_eligible=solo_eligible,
            partner_idle_seconds=max(0.0, idle),
            thoughts=tuple(deepcopy(state.get("thoughts", ()))),
        )
