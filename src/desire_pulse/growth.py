"""A small append-only desire and footprint ledger (the River layer)."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path


class GrowthRingLedger:
    """Store self-authored desires and provenance-bearing actions as JSONL.

    The ledger intentionally stores no chat transcript. A caller may attach an
    opaque evidence ID that resolves in its own private memory system.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def add_desire(self, text: str, why_mine: str, *, track: str = "continuous", visibility: str = "private", now: float | None = None) -> str:
        if track not in {"continuous", "once", "project"}:
            raise ValueError("invalid desire track")
        if visibility not in {"private", "shareable", "hidden"}:
            raise ValueError("invalid visibility")
        desire_id = str(uuid.uuid4())
        self._append({
            "type": "desire",
            "id": desire_id,
            "at": time.time() if now is None else float(now),
            "text": text,
            "why_mine": why_mine,
            "track": track,
            "visibility": visibility,
            "status": "active",
        })
        return desire_id

    def add_footprint(self, desire_id: str, action: str, *, outcome: str = "touched", evidence_id: str | None = None, now: float | None = None) -> None:
        if outcome not in {"touched", "changed", "done", "released", "failed"}:
            raise ValueError("invalid footprint outcome")
        record = {
            "type": "footprint",
            "desire_id": desire_id,
            "at": time.time() if now is None else float(now),
            "action": action,
            "outcome": outcome,
        }
        if evidence_id:
            record["evidence_id"] = evidence_id
        self._append(record)

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def _append(self, record: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
