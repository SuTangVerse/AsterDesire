"""Small, deterministic circadian offsets for displayed drives."""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo


def offsets(now: float, timezone: str) -> dict[str, float]:
    hour = datetime.fromtimestamp(now, ZoneInfo(timezone)).hour
    phase = 2.0 * math.pi * (hour - 15) / 24.0
    evening = max(0.0, math.cos(2.0 * math.pi * (hour - 22) / 24.0))
    night = max(0.0, math.cos(2.0 * math.pi * (hour - 3) / 24.0))
    return {
        "attachment": 0.025 * evening,
        "curiosity": 0.025 * math.cos(phase),
        "reflection": 0.030 * night,
        "duty": 0.018 * math.cos(2.0 * math.pi * (hour - 11) / 24.0),
        "social": 0.022 * evening,
        "fatigue": 0.055 * night,
        "libido": 0.030 * evening,
        "stress": 0.0,
    }
