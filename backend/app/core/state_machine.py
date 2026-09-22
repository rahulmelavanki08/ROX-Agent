import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ApplicationState(str, Enum):
    NOT_STARTED = 'NOT_STARTED'
    ANALYZING = 'ANALYZING'
    AWAITING_PLAN_APPROVAL = 'AWAITING_PLAN_APPROVAL'
    PLANNED = 'PLANNED'
    BUILDING_STATE = 'BUILDING_STATE'
    FILLING = 'FILLING'
    VERIFYING = 'VERIFYING'
    BLOCKED = 'BLOCKED'
    RECOVERING = 'RECOVERING'
    REVERIFYING = 'REVERIFYING'
    READY_FOR_REVIEW = 'READY_FOR_REVIEW'
    AWAITING_USER_SUBMISSION_APPROVAL = 'AWAITING_USER_SUBMISSION_APPROVAL'
    SUBMITTING = 'SUBMITTING'
    SUBMISSION_UNKNOWN = 'SUBMISSION_UNKNOWN'
    VERIFYING_SUBMISSION = 'VERIFYING_SUBMISSION'
    VERIFIED_SUCCESS = 'VERIFIED_SUCCESS'
    VERIFICATION_FAILED = 'VERIFICATION_FAILED'

class StateTransitionRecord(BaseModel):
    from_state: ApplicationState
    to_state: ApplicationState
    timestamp: float = Field(default_factory=time.time)
    reason: str
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    triggered_by: str = 'system'

class StateMachine:
    ALLOWED_TRANSITIONS = {
        ApplicationState.NOT_STARTED: [ApplicationState.ANALYZING],
        ApplicationState.ANALYZING: [ApplicationState.AWAITING_PLAN_APPROVAL, ApplicationState.BLOCKED, ApplicationState.VERIFICATION_FAILED],
        ApplicationState.AWAITING_PLAN_APPROVAL: [ApplicationState.PLANNED, ApplicationState.ANALYZING, ApplicationState.BLOCKED],
        ApplicationState.PLANNED: [ApplicationState.BUILDING_STATE, ApplicationState.BLOCKED],
        ApplicationState.BUILDING_STATE: [ApplicationState.FILLING, ApplicationState.BLOCKED],
        ApplicationState.FILLING: [ApplicationState.VERIFYING, ApplicationState.READY_FOR_REVIEW, ApplicationState.RECOVERING, ApplicationState.BLOCKED],
        ApplicationState.VERIFYING: [ApplicationState.FILLING, ApplicationState.READY_FOR_REVIEW, ApplicationState.RECOVERING, ApplicationState.BLOCKED],
        ApplicationState.BLOCKED: [ApplicationState.ANALYZING, ApplicationState.FILLING, ApplicationState.AWAITING_PLAN_APPROVAL, ApplicationState.RECOVERING],
        ApplicationState.RECOVERING: [ApplicationState.REVERIFYING, ApplicationState.BLOCKED, ApplicationState.VERIFICATION_FAILED],
        ApplicationState.REVERIFYING: [ApplicationState.FILLING, ApplicationState.VERIFYING, ApplicationState.RECOVERING, ApplicationState.READY_FOR_REVIEW, ApplicationState.VERIFICATION_FAILED],
        ApplicationState.READY_FOR_REVIEW: [ApplicationState.AWAITING_USER_SUBMISSION_APPROVAL, ApplicationState.BLOCKED, ApplicationState.FILLING],
        ApplicationState.AWAITING_USER_SUBMISSION_APPROVAL: [ApplicationState.SUBMITTING, ApplicationState.READY_FOR_REVIEW, ApplicationState.BLOCKED],
        ApplicationState.SUBMITTING: [ApplicationState.VERIFYING_SUBMISSION, ApplicationState.VERIFIED_SUCCESS, ApplicationState.SUBMISSION_UNKNOWN, ApplicationState.RECOVERING, ApplicationState.VERIFICATION_FAILED],
        ApplicationState.SUBMISSION_UNKNOWN: [ApplicationState.VERIFYING_SUBMISSION, ApplicationState.RECOVERING, ApplicationState.VERIFICATION_FAILED],
        ApplicationState.VERIFYING_SUBMISSION: [ApplicationState.VERIFIED_SUCCESS, ApplicationState.SUBMISSION_UNKNOWN, ApplicationState.VERIFICATION_FAILED],
        ApplicationState.VERIFIED_SUCCESS: [],
        ApplicationState.VERIFICATION_FAILED: [ApplicationState.ANALYZING]
    }

    def __init__(self, initial_state: ApplicationState = ApplicationState.NOT_STARTED):
        self.current_state = initial_state
        self.history: List[StateTransitionRecord] = []

    def can_transition(self, to_state: ApplicationState) -> bool:
        valid_targets = self.ALLOWED_TRANSITIONS.get(self.current_state, [])
        return to_state in valid_targets

    def transition(self, to_state: ApplicationState, reason: str, evidence: Optional[Dict[str, Any]] = None, triggered_by: str = 'system') -> StateTransitionRecord:
        if not self.can_transition(to_state):
            raise ValueError(f'Illegal transition from {self.current_state} to {to_state}. Allowed: {self.ALLOWED_TRANSITIONS.get(self.current_state)}')
        
        record = StateTransitionRecord(
            from_state=self.current_state,
            to_state=to_state,
            reason=reason,
            evidence_summary=evidence or {},
            triggered_by=triggered_by
        )
        self.history.append(record)
        self.current_state = to_state
        return record
