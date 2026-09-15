import unittest

from desire_pulse import DesireEngine, HeartbeatConfig, HeartbeatController


class HeartbeatTests(unittest.TestCase):
    def test_schedule_stays_in_range(self):
        controller = HeartbeatController(HeartbeatConfig(min_interval_seconds=100, max_interval_seconds=200))
        state = controller.new_state()
        wake = controller.schedule_next(state, 1000)
        self.assertGreaterEqual(wake, 1100)
        self.assertLessEqual(wake, 1200)

    def test_repeat_penalty_changes_close_scores(self):
        controller = HeartbeatController(HeartbeatConfig(quiet_start_hour=0, quiet_end_hour=0, repeat_penalty=0.3))
        state = controller.new_state()
        state["last_motive"] = "attachment"
        engine = DesireEngine()
        desire = engine.new_state(1000)
        desire["drives"]["attachment"] = 0.70
        desire["drives"]["curiosity"] = 0.65
        snap = engine.snapshot(desire, 1000)
        decision = controller.elect(state, snap, 1000)
        self.assertEqual(decision.motive, "curiosity")

    def test_failures_open_and_recover_circuit(self):
        cfg = HeartbeatConfig(circuit_breaker_failures=3)
        controller = HeartbeatController(cfg)
        state = controller.new_state()
        for index in range(3):
            controller.record_result(state, "failed", 100 + index)
        self.assertTrue(state["halted"])
        controller.recover(state, 1000)
        self.assertFalse(state["halted"])
        self.assertEqual(state["consecutive_failures"], 0)

    def test_skip_defers_same_action(self):
        controller = HeartbeatController(HeartbeatConfig(skip_cooldown_seconds=100))
        state = controller.new_state()
        state["last_action"] = "create"
        controller.record_result(state, "skipped", 50, action="create")
        self.assertEqual(state["skipped_until"]["create"], 150)

    def test_libido_motive_stays_private(self):
        controller = HeartbeatController(
            HeartbeatConfig(quiet_start_hour=0, quiet_end_hour=0)
        )
        engine = DesireEngine()
        state = engine.new_state(100)
        state["drives"]["libido"] = 0.95
        snapshot = engine.snapshot(state, 100)
        decision = controller.elect(controller.new_state(), snapshot, 100)
        self.assertFalse(decision.should_contact)
        self.assertEqual(decision.action, "private_reverie")

    def test_decision_result_receipt_is_idempotent(self):
        controller = HeartbeatController()
        state = controller.new_state()
        controller.record_result(state, "completed", 100, action="create", decision_id="wake-1")
        controller.record_result(state, "completed", 100, action="create", decision_id="wake-1")
        self.assertEqual(len(state["activity_history"]), 1)


if __name__ == "__main__":
    unittest.main()
