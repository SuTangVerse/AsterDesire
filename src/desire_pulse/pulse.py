"""Derived physiological display state. It stores no raw conversation text."""

from __future__ import annotations

import math
import time

from .engine import clamp
from .models import EventSignals, PulseConfig, PulseSnapshot, Snapshot


class PulseEngine:
    def __init__(self, config: PulseConfig | None = None):
        self.config = config or PulseConfig()

    def new_state(self, now: float | None = None) -> dict:
        now = time.time() if now is None else float(now)
        return {"version": 1, "updated_at": now, "affect": {}, "sensory": {}, "history": []}

    def observe(self, state: dict, event: EventSignals, now: float | None = None) -> dict:
        now = time.time() if now is None else float(now)
        state = self._advance(state, now)
        present = event.current_action and not event.third_party and not event.technical_only
        additions = {
            "positive": event.positive,
            "negative": event.negative,
            "intimate": event.intimacy if present else 0.0,
            "aroused": event.sexual if present else 0.0,
            "startled": event.startling,
            "focused": event.technical,
        }
        for name, amount in additions.items():
            if amount > 0:
                state["affect"][name] = clamp(state["affect"].get(name, 0.0) + amount)
        for name in ("touch", "smell", "taste", "sound"):
            amount = clamp(getattr(event, name))
            if amount > 0 and present:
                state["sensory"][name] = clamp(state["sensory"].get(name, 0.0) + amount)
        return state

    def snapshot(self, state: dict, desire: Snapshot, now: float | None = None) -> tuple[dict, PulseSnapshot]:
        now = time.time() if now is None else float(now)
        state = self._advance(state, now)
        affect = state["affect"]
        undertone = max(affect, key=affect.get) if affect else "neutral"
        intensity = affect.get(undertone, 0.0)
        hr = self.config.resting_heart_rate
        hr += 20 * desire.arousal + 8 * desire.drives["stress"] + 5 * intensity
        temp = self.config.resting_temperature + 0.55 * desire.arousal + 0.12 * intensity
        breathing = "quick" if hr >= 88 else "deep" if desire.drives["fatigue"] >= 0.62 else "steady"
        chord = {
            "negative": "Am7",
            "intimate": "Fmaj7",
            "aroused": "Dm7",
            "startled": "Bdim7",
            "focused": "Cmaj7",
            "positive": "Gmaj7",
        }.get(undertone, "Cmaj7")
        sensory = {name: round(value, 4) for name, value in state["sensory"].items()}
        result = PulseSnapshot(now, round(hr), round(temp, 1), breathing, chord, undertone, sensory)
        state["history"].append({
            "at": now,
            "heart_rate": result.heart_rate,
            "temperature": result.temperature,
            "breathing": result.breathing,
            "chord": result.chord,
            "undertone": result.undertone,
            "sensory": sensory,
        })
        state["history"] = state["history"][-self.config.sample_history_limit :]
        return state, result

    def _advance(self, state: object, now: float) -> dict:
        if not isinstance(state, dict) or state.get("version") != 1:
            state = self.new_state(now)
        state.setdefault("affect", {})
        state.setdefault("sensory", {})
        state.setdefault("history", [])
        elapsed = max(0.0, now - float(state.get("updated_at", now)))
        decay = math.pow(0.5, elapsed / self.config.affect_half_life_seconds)
        state["affect"] = {
            name: value * decay
            for name, value in state["affect"].items()
            if value * decay >= 0.01
        }
        state["sensory"] = {
            name: value * math.pow(0.5, elapsed / self.config.sensory_half_lives[name])
            for name, value in state["sensory"].items()
            if name in self.config.sensory_half_lives
            and value * math.pow(0.5, elapsed / self.config.sensory_half_lives[name]) >= 0.01
        }
        state["updated_at"] = now
        return state
