import json
import tempfile
import unittest
from pathlib import Path

from desire_pulse import AgentConfig, AgentRuntime, EventSignals, JsonStateStore


class RuntimeTests(unittest.TestCase):
    def test_observe_and_wake_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            runtime = AgentRuntime(JsonStateStore(path), AgentConfig(timezone="UTC"))
            observed = runtime.observe(EventSignals("m1", positive=0.8), 12 * 3600)
            self.assertIn("pulse", observed)
            result = runtime.wake(lambda decision, context: {"status": "silent"}, 16 * 3600)
            self.assertIn("decision", result)
            data = json.loads(path.read_text())
            self.assertIn("heartbeat", data)

    def test_handler_failure_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = AgentRuntime(JsonStateStore(Path(directory) / "state.json"))

            def broken(decision, context):
                raise RuntimeError("secret details must not escape")

            result = runtime.wake(broken, 12 * 3600)
            self.assertEqual(result["outcome"], {"status": "failed", "error": "RuntimeError"})


if __name__ == "__main__":
    unittest.main()
