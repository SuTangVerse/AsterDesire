import tempfile
import unittest
from pathlib import Path

from desire_pulse import AgentRuntime, HeartbeatLoop, JsonStateStore


class HeartbeatLoopTests(unittest.TestCase):
    def test_tick_schedules_then_runs_when_due(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = AgentRuntime(JsonStateStore(Path(directory) / "state.json"))
            calls = []

            def handler(decision, context):
                calls.append(decision.action)
                return {"status": "silent"}

            loop = HeartbeatLoop(runtime, handler)
            self.assertIsNone(loop.tick(12 * 3600))
            state = runtime.store.load()
            due = state["heartbeat"]["next_wake_at"]
            self.assertIsNotNone(loop.tick(due))
            self.assertEqual(len(calls), 1)
