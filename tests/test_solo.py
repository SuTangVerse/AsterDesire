import unittest

from desire_pulse import DesireConfig, DesireEngine, SoloController


class SoloControllerTests(unittest.TestCase):
    def eligible_state(self):
        config = DesireConfig(libido_threshold=0.65, solo_idle_seconds=10)
        engine = DesireEngine(config)
        state = engine.new_state(0)
        state["updated_at"] = 1
        state["last_partner_at"] = 1
        state["drives"]["libido"] = 0.92
        return config, state, engine.snapshot(state, 100)

    def test_complete_is_receipt_idempotent(self):
        config, state, snapshot = self.eligible_state()
        solo = SoloController(config)
        self.assertTrue(solo.begin(state, snapshot, 100).allowed)
        solo.stimulate(state, 0.8, 110)
        self.assertTrue(solo.complete(state, "release-1", 120))
        libido = state["drives"]["libido"]
        self.assertFalse(solo.complete(state, "release-1", 121))
        self.assertEqual(state["drives"]["libido"], libido)

    def test_interruption_does_not_count_as_release(self):
        config, state, snapshot = self.eligible_state()
        solo = SoloController(config)
        solo.begin(state, snapshot, 100)
        solo.interrupt(state, 105)
        self.assertEqual(state["solo"]["status"], "interrupted")
        self.assertEqual(state["solo"]["count"], 0)


if __name__ == "__main__":
    unittest.main()
