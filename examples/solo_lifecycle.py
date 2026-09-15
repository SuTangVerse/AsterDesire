"""Exercise the public solo state machine without private content."""

from desire_pulse import DesireConfig, DesireEngine, SoloController


config = DesireConfig(libido_threshold=0.65, solo_idle_seconds=10)
engine = DesireEngine(config)
solo = SoloController(config, timezone="UTC", seed="example-agent")

state = engine.new_state(0)
state["last_partner_at"] = 1
state["drives"]["libido"] = 0.90
snapshot = engine.snapshot(state, 100)

eligibility = solo.begin(state, snapshot, 100)
print("begin:", eligibility)
if eligibility.allowed:
    solo.stimulate(state, intensity=0.6, now=110)
    solo.interrupt(state, now=120)
    print("interrupted:", state["solo"])
