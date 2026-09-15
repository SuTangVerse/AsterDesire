"""Optional async loop for deployments that do not already have a scheduler."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from .runtime import ActionHandler, AgentRuntime


class HeartbeatLoop:
    def __init__(self, runtime: AgentRuntime, handler: ActionHandler, *, poll_seconds: float = 5.0):
        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")
        self.runtime = runtime
        self.handler = handler
        self.poll_seconds = poll_seconds

    def tick(self, now: float | None = None) -> dict | None:
        if not self.runtime.heartbeat_due(now):
            return None
        return self.runtime.wake(self.handler, now)

    async def run(self, stop: Callable[[], bool]) -> None:
        """Poll until ``stop`` returns true; cancellation is propagated."""
        while not stop():
            self.tick()
            await asyncio.sleep(self.poll_seconds)
