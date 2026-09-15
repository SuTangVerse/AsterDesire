import json
import tempfile
import unittest
from pathlib import Path

from desire_pulse import load_config


class ConfigTests(unittest.TestCase):
    def test_json_loader_builds_nested_dataclasses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({
                "timezone": "UTC",
                "desire": {"solo_modes": ["fantasy", "mixed"]},
                "heartbeat": {"daily_limit": 3},
            }))
            config = load_config(path)
            self.assertEqual(config.desire.solo_modes, ("fantasy", "mixed"))
            self.assertEqual(config.heartbeat.daily_limit, 3)
