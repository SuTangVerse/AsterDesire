"""Configuration and value objects.

Defaults are deliberately illustrative. They are not copied from a private
persona and should be calibrated for each deployment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


DRIVES = (
    "attachment",
    "curiosity",
    "reflection",
    "duty",
    "social",
    "fatigue",
    "libido",
    "stress",
)


def default_baselines() -> dict[str, float]:
    return {
        "attachment": 0.40,
        "curiosity": 0.46,
        "reflection": 0.34,
        "duty": 0.38,
        "social": 0.28,
        "fatigue": 0.18,
        "libido": 0.24,
        "stress": 0.10,
    }


def default_drift() -> dict[str, float]:
    return {
        "attachment": 0.012,
        "curiosity": 0.014,
        "reflection": 0.007,
        "duty": 0.006,
        "social": 0.008,
        "fatigue": 0.004,
        "libido": 0.009,
        "stress": -0.008,
    }


def default_coupling() -> dict[str, float]:
    return {
        "attachment>social": 0.012,
        "attachment>libido": 0.014,
        "curiosity>reflection": 0.016,
        "duty>stress": 0.020,
        "stress>fatigue": 0.025,
        "fatigue>curiosity": -0.026,
        "fatigue>social": -0.021,
    }


def default_plateaus() -> dict[str, int]:
    return {
        "attachment": 80 * 60,
        "curiosity": 95 * 60,
        "reflection": 70 * 60,
        "duty": 100 * 60,
        "social": 75 * 60,
        "libido": 85 * 60,
        "stress": 40 * 60,
    }


def default_sensory_half_lives() -> dict[str, int]:
    return {
        "touch": 18 * 60,
        "smell": 13 * 60,
        "taste": 9 * 60,
        "sound": 11 * 60,
    }


@dataclass(frozen=True)
class DesireConfig:
    baselines: Mapping[str, float] = field(default_factory=default_baselines)
    hourly_drift: Mapping[str, float] = field(default_factory=default_drift)
    coupling: Mapping[str, float] = field(default_factory=default_coupling)
    plateau_seconds: Mapping[str, int] = field(default_factory=default_plateaus)
    baseline_pull_hours: float = 20.0
    libido_threshold: float = 0.70
    solo_idle_seconds: float = 60 * 60
    solo_fatigue_ceiling: float = 0.70
    refractory_seconds: float = 2.5 * 3600
    solo_daily_limit: int = 2
    solo_modes: tuple[str, ...] = ("fantasy", "body", "mixed")
    solo_release_libido_relief: float = 0.48
    thought_threshold: float = 0.64
    thought_ttl_seconds: int = 4 * 3600
    thought_history_limit: int = 16


@dataclass(frozen=True)
class PulseConfig:
    resting_heart_rate: float = 68.0
    resting_temperature: float = 36.6
    affect_half_life_seconds: float = 32 * 60
    sample_history_limit: int = 720
    sensory_half_lives: Mapping[str, int] = field(default_factory=default_sensory_half_lives)


@dataclass(frozen=True)
class HeartbeatConfig:
    # Illustrative defaults, intentionally not a production persona's values.
    min_interval_seconds: int = 35 * 60
    max_interval_seconds: int = 165 * 60
    daily_limit: int = 5
    quiet_start_hour: int = 1
    quiet_end_hour: int = 8
    repeat_penalty: float = 0.22
    skip_cooldown_seconds: int = 95 * 60
    failure_backoff_seconds: tuple[int, ...] = (120, 600, 1800)
    circuit_breaker_failures: int = 4


@dataclass(frozen=True)
class AgentConfig:
    desire: DesireConfig = field(default_factory=DesireConfig)
    pulse: PulseConfig = field(default_factory=PulseConfig)
    heartbeat: HeartbeatConfig = field(default_factory=HeartbeatConfig)
    timezone: str = "UTC"
    seed: str = "public-example"


@dataclass(frozen=True)
class EventSignals:
    """Already-classified event features; never include raw message text."""

    event_id: str
    source: str = "chat"
    intimacy: float = 0.0
    sexual: float = 0.0
    positive: float = 0.0
    negative: float = 0.0
    technical: float = 0.0
    social: float = 0.0
    startling: float = 0.0
    touch: float = 0.0
    smell: float = 0.0
    taste: float = 0.0
    sound: float = 0.0
    partner_present: bool = True
    current_action: bool = True
    third_party: bool = False
    technical_only: bool = False
    stop: bool = False
    resume: bool = False
    climax: bool = False


@dataclass(frozen=True)
class Snapshot:
    at: float
    drives: Mapping[str, float]
    strongest_drive: str
    intent: str
    arousal: float
    reserve: float
    refractory: bool
    reverie_eligible: bool
    solo_eligible: bool
    partner_idle_seconds: float
    thoughts: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class PulseSnapshot:
    at: float
    heart_rate: int
    temperature: float
    breathing: str
    chord: str
    undertone: str
    sensory: Mapping[str, float]


@dataclass(frozen=True)
class HeartbeatDecision:
    decision_id: str
    at: float
    action: str
    motive: str
    should_contact: bool
    reason: str
    next_wake_at: float
