import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class LedgerEntry(BaseModel):
    step_id: str
    action: str
    actor: str = 'system'
    timestamp: float = Field(default_factory=time.time)
    formatted_time: str = ''
    preconditions: List[str] = Field(default_factory=list)
    command_or_operation: str = ''
    observation: Dict[str, Any] = Field(default_factory=dict)
    postconditions: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    status: str = 'PENDING'
    attempt: int = 1
    recovery_details: Optional[Dict[str, Any]] = None
    state_transition: Optional[str] = None
    verification_result: str = ''
    previous_hash: str = ''
    entry_hash: str = ''

    def compute_hash(self) -> str:
        payload = {
            'step_id': self.step_id,
            'action': self.action,
            'timestamp': self.timestamp,
            'status': self.status,
            'evidence': self.evidence,
            'previous_hash': self.previous_hash
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

class ProofLedger:
    def __init__(self, application_id: str, storage_dir: Path):
        self.application_id = application_id
        self.app_dir = storage_dir / 'applications' / application_id
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_file = self.app_dir / 'ledger.json'
        self.entries: List[LedgerEntry] = []
        self._load()

    def _load(self):
        if self.ledger_file.exists():
            try:
                with open(self.ledger_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = [LedgerEntry(**d) for d in data]
            except Exception:
                self.entries = []

    def save(self):
        with open(self.ledger_file, 'w', encoding='utf-8') as f:
            json.dump([e.model_dump() for e in self.entries], f, indent=2)

    def append(self, entry: LedgerEntry) -> LedgerEntry:
        import datetime
        entry.formatted_time = datetime.datetime.fromtimestamp(entry.timestamp).strftime('%H:%M:%S')
        if self.entries:
            entry.previous_hash = self.entries[-1].entry_hash
        else:
            entry.previous_hash = '0' * 64
        entry.entry_hash = entry.compute_hash()
        self.entries.append(entry)
        self.save()
        return entry

    def get_all(self) -> List[Dict[str, Any]]:
        return [e.model_dump() for e in self.entries]
