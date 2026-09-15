import unittest

from desire_pulse import DesireConfig, DesireEngine, EventSignals


class DesireEngineTests(unittest.TestCase):
    def test_duplicate_event_is_idempotent(self):
        engine = DesireEngine(timezone="UTC")
        state = engine.new_state(1000)
        event = EventSignals("same", intimacy=0.8, sexual=0.6)
        state, first = engine.apply_event(state, event, 1000)
        state, second = engine.apply_event(state, event, 1000)
        self.assertEqual(first.drives, second.drives)
        self.assertEqual(first.arousal, second.arousal)

    def test_state_contains_no_raw_text(self):
        engine = DesireEngine()
        state, _ = engine.apply_event(engine.new_state(10), EventSignals("opaque-event", positive=1), 10)
        serialized = repr(state)
        self.assertNotIn("message", serialized.lower())
        self.assertIn("opaque-event", serialized)

    def test_libido_does_not_ignite_arousal(self):
        cfg = DesireConfig(libido_threshold=0.70, solo_idle_seconds=10)
        engine = DesireEngine(cfg)
        state = engine.new_state(0)
        state["drives"]["libido"] = 0.9
        state["last_partner_at"] = 1
        state["updated_at"] = 1
        before = engine.snapshot(state, 100)
        self.assertTrue(before.reverie_eligible)
        self.assertTrue(before.solo_eligible)
        state, after = engine.advance(state, 100)
        self.assertEqual(after.arousal, before.arousal)

    def test_climax_starts_refractory_and_reduces_reserve(self):
        engine = DesireEngine()
        state = engine.new_state(0)
        state, snap = engine.apply_event(state, EventSignals("release", sexual=1, climax=True), 10)
        self.assertTrue(snap.refractory)
        self.assertLess(snap.reserve, 0.2)

    def test_third_party_or_hypothetical_signal_does_not_raise_libido(self):
        engine = DesireEngine()
        state = engine.new_state(10)
        before = state["drives"]["libido"]
        state, _ = engine.apply_event(
            state,
            EventSignals("quoted", sexual=1.0, third_party=True),
            10,
        )
        self.assertEqual(state["drives"]["libido"], before)

    def test_structural_thought_can_be_consumed(self):
        config = DesireConfig(thought_threshold=0.60)
        engine = DesireEngine(config)
        state = engine.new_state(0)
        state["drives"]["curiosity"] = 0.90
        state, snapshot = engine.advance(state, 3600)
        self.assertEqual(snapshot.thoughts[0]["drive"], "curiosity")
        consumed = engine.consume_thought(state, "curiosity")
        self.assertEqual(consumed["drive"], "curiosity")

    def test_satisfaction_plateau_blocks_immediate_refill(self):
        engine = DesireEngine()
        state = engine.new_state(0)
        state["drives"]["curiosity"] = 0.90
        state, _ = engine.satisfy(state, "explore", 10)
        after_satisfaction = state["drives"]["curiosity"]
        state, _ = engine.advance(state, 20)
        self.assertLessEqual(state["drives"]["curiosity"], after_satisfaction)



if __name__ == "__main__":
    unittest.main()
