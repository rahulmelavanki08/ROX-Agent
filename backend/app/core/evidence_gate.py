import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.core.action_contract import ActionContract, ActionStatus, RiskLevel

class GateEvaluation(BaseModel):
    passed: bool
    verdict: str
    reasons: List[str] = Field(default_factory=list)
    deterministic_evidence: Dict[str, Any] = Field(default_factory=dict)
    can_proceed: bool = False
    requires_user_approval: bool = False

class EvidenceGate:
    @staticmethod
    def evaluate_action_contract(contract: ActionContract) -> GateEvaluation:
        reasons = []
        evidence = contract.evidence or {}

        if contract.precondition_results:
            failed_pre = [k for k, v in contract.precondition_results.items() if not v]
            if failed_pre:
                reasons.append(f'Preconditions failed: {failed_pre}')

        if contract.postcondition_results:
            failed_post = [k for k, v in contract.postcondition_results.items() if not v]
            if failed_post:
                reasons.append(f'Postconditions failed: {failed_post}')
        elif not contract.postconditions:
            reasons.append('No deterministic postconditions defined for action contract')

        if not evidence:
            reasons.append('No machine-checkable evidence provided')

        if contract.error_message:
            reasons.append(f'Action recorded error: {contract.error_message}')

        passed = len(reasons) == 0
        requires_user_approval = (contract.risk_level == RiskLevel.HIGH and not evidence.get('user_approval_granted', False))
        if requires_user_approval:
            passed = False
            reasons.append('HIGH RISK action requires explicit user authorization before execution')

        verdict = 'GATE_APPROVED' if passed else 'GATE_REJECTED'

        return GateEvaluation(
            passed=passed,
            verdict=verdict,
            reasons=reasons,
            deterministic_evidence=evidence,
            can_proceed=passed and not requires_user_approval,
            requires_user_approval=requires_user_approval
        )

    @staticmethod
    def evaluate_final_submission(
        fields_status: Dict[str, str],
        documents_status: Dict[str, str],
        unresolved_conflicts: List[Dict[str, Any]],
        submission_payload: Dict[str, Any],
        user_approved_irreversible: bool
    ) -> GateEvaluation:
        reasons = []
        evidence = {}

        if not user_approved_irreversible:
            reasons.append('User has not explicitly approved the irreversible final submission')

        if unresolved_conflicts:
            reasons.append(f'{len(unresolved_conflicts)} unresolved cross-document data conflicts exist')

        unverified_fields = [f for f, status in fields_status.items() if status != 'VERIFIED']
        if unverified_fields:
            reasons.append(f'{len(unverified_fields)} critical fields are not verified: {unverified_fields[:3]}')

        unverified_docs = [d for d, status in documents_status.items() if status != 'VERIFIED']
        if unverified_docs:
            reasons.append(f'{len(unverified_docs)} mandatory documents are not verified: {unverified_docs}')

        ref_no = submission_payload.get('reference_number', '')
        if not ref_no or not re.match(r'^SCH-2026-\d{4,6}$', str(ref_no)):
            reasons.append(f'Invalid or missing application reference number: {ref_no}')
        else:
            evidence['reference_number'] = ref_no

        portal_status = str(submission_payload.get('portal_status', '')).lower()
        if portal_status not in ['submitted', 'accepted', 'completed']:
            reasons.append(f'Portal status is not confirmed submitted: {portal_status}')
        else:
            evidence['portal_status'] = portal_status

        timestamp = submission_payload.get('submitted_at')
        if not timestamp:
            reasons.append('Portal submission timestamp is missing from server response')
        else:
            evidence['submitted_at'] = timestamp

        passed = len(reasons) == 0
        verdict = 'VERIFIED_SUCCESS' if passed else 'VERIFICATION_FAILED'

        return GateEvaluation(
            passed=passed,
            verdict=verdict,
            reasons=reasons,
            deterministic_evidence=evidence,
            can_proceed=passed,
            requires_user_approval=not user_approved_irreversible
        )
