"""Load public configuration without executing code from configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .models import AgentConfig, DesireConfig, HeartbeatConfig, PulseConfig


def config_from_mapping(value: Mapping[str, object]) -> AgentConfig:
    desire_data = dict(value.get("desire", {}) or {})
    pulse_data = dict(value.get("pulse", {}) or {})
    heartbeat_data = dict(value.get("heartbeat", {}) or {})
    if "solo_modes" in desire_data:
        desire_data["solo_modes"] = tuple(desire_data["solo_modes"])
    if "failure_backoff_seconds" in heartbeat_data:
        heartbeat_data["failure_backoff_seconds"] = tuple(heartbeat_data["failure_backoff_seconds"])
    return AgentConfig(
        desire=DesireConfig(**desire_data),
        pulse=PulseConfig(**pulse_data),
        heartbeat=HeartbeatConfig(**heartbeat_data),
        timezone=str(value.get("timezone", "UTC")),
        seed=str(value.get("seed", "public-example")),
    )


def load_config(path: str | Path) -> AgentConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("configuration root must be an object")
    return config_from_mapping(data)
