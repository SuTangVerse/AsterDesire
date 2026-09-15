import unittest

from desire_pulse import DesireEngine, EventSignals, PulseConfig
from desire_pulse.pulse import PulseEngine


class PulseTests(unittest.TestCase):
    def test_current_sensory_signal_decays(self):
        engine = DesireEngine()
        desire = engine.snapshot(engine.new_state(0), 0)
        pulse = PulseEngine(PulseConfig())
        state = pulse.new_state(0)
        state = pulse.observe(state, EventSignals("touch", touch=0.8), 0)
        state, first = pulse.snapshot(state, desire, 0)
        state, later = pulse.snapshot(state, desire, 3600)
        self.assertGreater(first.sensory["touch"], later.sensory.get("touch", 0.0))

    def test_third_party_sensory_signal_is_ignored(self):
        pulse = PulseEngine()
        state = pulse.new_state(0)
        state = pulse.observe(state, EventSignals("quoted-touch", touch=1.0, third_party=True), 0)
        self.assertEqual(state["sensory"], {})

    def test_third_party_intimacy_does_not_create_aroused_affect(self):
        pulse = PulseEngine()
        state = pulse.new_state(0)
        state = pulse.observe(
            state,
            EventSignals("quoted-intimacy", intimacy=1.0, sexual=1.0, third_party=True),
            0,
        )
        self.assertNotIn("intimate", state["affect"])
        self.assertNotIn("aroused", state["affect"])


if __name__ == "__main__":
    unittest.main()
