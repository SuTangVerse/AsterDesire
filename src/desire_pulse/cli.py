"""Tiny inspection/demo CLI."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from .models import EventSignals
from .runtime import AgentRuntime
from .storage import JsonStateStore


def main() -> None:
    parser = argparse.ArgumentParser(prog="desire-pulse")
    parser.add_argument("command", choices=("demo", "inspect"))
    parser.add_argument("--state", default="state/agent.json")
    args = parser.parse_args()
    path = Path(args.state)
    if args.command == "demo":
        path = Path(tempfile.mkdtemp(prefix="desire-pulse-demo-")) / "state.json"
    runtime = AgentRuntime(JsonStateStore(path))
    if args.command == "demo":
        now = time.time()
        observed = runtime.observe(EventSignals("demo-1", intimacy=0.55, positive=0.7), now)
        result = runtime.wake(lambda decision, context: {"status": "silent"}, now + 4 * 3600)
        print(json.dumps({
            "state_path": str(path),
            "observed": {key: asdict(value) for key, value in observed.items()},
            "wake": {key: asdict(value) if hasattr(value, "__dataclass_fields__") else value for key, value in result.items()},
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(JsonStateStore(path).load(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
