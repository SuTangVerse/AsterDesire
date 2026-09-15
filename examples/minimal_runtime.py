"""Run one observation and one heartbeat without any external service."""

from dataclasses import asdict
from pathlib import Path

from desire_pulse import AgentRuntime, EventSignals, JsonStateStore


runtime = AgentRuntime(JsonStateStore(Path("state/example-agent.json")))
runtime.observe(EventSignals(event_id="example-message-1", positive=0.8, social=0.4))


def local_action(decision, context):
    print("decision:", asdict(decision))
    print("context:", context)
    # Replace this with an LLM call, message sender, or local creative action.
    return {"status": "completed", "reason": "example action finished"}


print(runtime.wake(local_action))
