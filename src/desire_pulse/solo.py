"""Standalone solo lifecycle with no private fantasy content or lexicon."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from .models import DesireConfig, Snapshot


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class SoloEligibility:
    allowed: bool
    reasons: tuple[str, ...]
    suggested_mode: str


class SoloController:
    """Manage eligibility, active phases, interruption, and idempotent release.

    Libido selects eligibility while arousal remains an independently observed
    body state. The controller contains no
    erotic prose, body vocabulary, device list, or persona-specific behaviour.
    """

    def __init__(self, config: DesireConfig | None = None, *, timezone: str = "UTC", seed: str = "public-example"):
        self.config = config or DesireConfig()
        self.timezone = timezone
        self.seed = seed

    def eligibility(self, state: dict, snapshot: Snapshot, now: float | None = None) -> SoloEligibility:
        now = time.time() if now is None else float(now)
        solo = self._ensure(state)
        self._roll_day(solo, now)
        reasons: list[str] = []
        if not snapshot.solo_eligible:
            reasons.append("desire_conditions")
        if solo["status"] == "active":
            reasons.append("already_active")
        if solo["count"] >= self.config.solo_daily_limit:
            reasons.append("daily_limit")
        if snapshot.refractory:
            reasons.append("refractory")
        return SoloEligibility(not reasons, tuple(reasons), self._mode(now))

    def begin(self, state: dict, snapshot: Snapshot, now: float | None = None, *, mode: str | None = None) -> SoloEligibility:
        now = time.time() if now is None else float(now)
        result = self.eligibility(state, snapshot, now)
        if not result.allowed:
            return result
        selected = mode or result.suggested_mode
        if selected not in self.config.solo_modes:
            raise ValueError("unsupported solo mode")
        solo = self._ensure(state)
        solo.update(status="active", mode=selected, started_at=now, last_at=now)
        return SoloEligibility(True, (), selected)

    def stimulate(self, state: dict, intensity: float, now: float | None = None) -> None:
        now = time.time() if now is None else float(now)
        solo = self._ensure(state)
        if solo["status"] != "active":
            raise RuntimeError("solo session is not active")
        intensity = _clamp(intensity)
        state["arousal"] = _clamp(float(state.get("arousal", 0.0)) + 0.30 * intensity)
        state["reserve"] = _clamp(float(state.get("reserve", 1.0)) - 0.04 * intensity)
        solo["last_at"] = now

    def complete(self, state: dict, receipt_id: str, now: float | None = None, *, released: bool = True) -> bool:
        now = time.time() if now is None else float(now)
        if not receipt_id:
            raise ValueError("receipt_id is required")
        solo = self._ensure(state)
        receipts = solo.setdefault("release_receipts", [])
        if receipt_id in receipts:
            return False
        if solo["status"] != "active":
            raise RuntimeError("solo session is not active")
        if released:
            state["arousal"] = 0.05
            state["reserve"] = 0.16
            state["refractory_until"] = now + self.config.refractory_seconds
            state["drives"]["libido"] = _clamp(
                state["drives"]["libido"] - self.config.solo_release_libido_relief
            )
            receipts.append(receipt_id)
            solo["release_receipts"] = receipts[-64:]
            solo["count"] += 1
        solo.update(status="idle", mode="none", last_at=now)
        return True

    def interrupt(self, state: dict, now: float | None = None) -> None:
        now = time.time() if now is None else float(now)
        solo = self._ensure(state)
        if solo["status"] == "active":
            solo.update(status="interrupted", mode="none", interrupted_at=now, last_at=now)

    def reset_interruption(self, state: dict) -> None:
        solo = self._ensure(state)
        if solo["status"] == "interrupted":
            solo["status"] = "idle"

    def _mode(self, now: float) -> str:
        modes = self.config.solo_modes
        if not modes:
            raise ValueError("solo_modes cannot be empty")
        bucket = int(now // 3600)
        digest = hashlib.sha256(f"{self.seed}:solo:{bucket}".encode()).digest()
        return modes[int.from_bytes(digest[:4], "big") % len(modes)]

    def _ensure(self, state: dict) -> dict:
        template = {
            "status": "idle", "mode": "none", "started_at": 0.0,
            "last_at": 0.0, "interrupted_at": 0.0, "day": "", "count": 0,
            "release_receipts": [],
        }
        solo = state.setdefault("solo", template.copy())
        for key, value in template.items():
            solo.setdefault(key, value)
        return solo

    def _roll_day(self, solo: dict, now: float) -> None:
        day = datetime.fromtimestamp(now, ZoneInfo(self.timezone)).date().isoformat()
        if solo["day"] != day:
            solo["day"] = day
            solo["count"] = 0
