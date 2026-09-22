import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = 'LOW'          # Fill field, save draft, change select
    MEDIUM = 'MEDIUM'    # Replace file, modify critical field
    HIGH = 'HIGH'        # Final submit, payment, cancel application

class ActionStatus(str, Enum):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    VERIFIED = 'VERIFIED'
    FAILED = 'FAILED'
    RECOVERING = 'RECOVERING'
    BLOCKED = 'BLOCKED'

class ActionContract(BaseModel):
    action_id: str
    name: str
    step_category: str = 'form_fill'
    risk_level: RiskLevel = RiskLevel.LOW
    preconditions: List[str] = Field(default_factory=list)
    precondition_results: Dict[str, bool] = Field(default_factory=dict)
    execution_command: str = ''
    execution_params: Dict[str, Any] = Field(default_factory=dict)
    observation: Dict[str, Any] = Field(default_factory=dict)
    postconditions: List[str] = Field(default_factory=list)
    postcondition_results: Dict[str, bool] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    attempt: int = 1
    max_attempts: int = 3
    error_message: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None

    def mark_in_progress(self):
        self.status = ActionStatus.IN_PROGRESS

    def record_observation(self, obs: Dict[str, Any]):
        self.observation = obs

    def complete_verified(self, evidence: Dict[str, Any]):
        self.evidence = evidence
        self.status = ActionStatus.VERIFIED
        self.completed_at = time.time()

    def complete_failed(self, error: str, evidence: Optional[Dict[str, Any]] = None):
        self.status = ActionStatus.FAILED
        self.error_message = error
        if evidence:
            self.evidence = evidence
        self.completed_at = time.time()
