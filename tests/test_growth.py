import tempfile
import unittest
from pathlib import Path

from desire_pulse import GrowthRingLedger


class GrowthRingTests(unittest.TestCase):
    def test_desire_and_footprint_keep_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = GrowthRingLedger(Path(directory) / "rings.jsonl")
            desire_id = ledger.add_desire("Learn a new craft", "Chosen by the agent", now=10)
            ledger.add_footprint(desire_id, "Made a small study", evidence_id="opaque-7", now=20)
            records = ledger.records()
            self.assertEqual(records[1]["desire_id"], desire_id)
            self.assertEqual(records[1]["evidence_id"], "opaque-7")


if __name__ == "__main__":
    unittest.main()
