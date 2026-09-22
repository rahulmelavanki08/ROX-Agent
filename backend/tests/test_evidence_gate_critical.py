import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.action_contract import ActionContract, ActionStatus, RiskLevel
from app.core.evidence_gate import EvidenceGate, GateEvaluation

def test_critical_zero_trust_llm_hallucination_blocked():
    """
    CRITICAL ZERO-TRUST CONTRACT TEST:
    Prove that if the LLM claims an action or submission is completed successfully,
    but deterministic verifiers detect failure or missing evidence,
    the Evidence Gate unconditionally REJECTS the proposal and forbids
    transition to VERIFIED or VERIFIED_SUCCESS.
    """
    # 1. Action Contract Test: LLM claims action succeeded, but postconditions failed
    contract = ActionContract(
        action_id="ACT_TEST_ZERO_TRUST",
        name="Upload Financial Proof",
        step_category="document_upload",
        risk_level=RiskLevel.LOW,
        preconditions=["file_exists"],
        precondition_results={"file_exists": True},
        execution_command="mock_upload()",
        postconditions=["status_200_ok", "server_checksum_match"],
        postcondition_results={"status_200_ok": False, "server_checksum_match": False}, # Deterministic failure!
        evidence={"llm_verdict": "I believe the upload was successful."}
    )

    evaluation = EvidenceGate.evaluate_action_contract(contract)
    assert evaluation.passed is False
    assert evaluation.verdict == "GATE_REJECTED"
    assert any("Postconditions failed" in r for r in evaluation.reasons)

    # 2. Final Submission Test: LLM proposes VERIFIED_SUCCESS, but reference number is fake or missing
    fields_status = {"full_name": "VERIFIED", "date_of_birth": "VERIFIED", "annual_income": "VERIFIED"}
    docs_status = {"doc_aadhaar": "VERIFIED", "doc_marksheet": "VERIFIED"}
    
    # Payload has no valid reference number from portal
    fraudulent_payload = {
        "llm_claim": "The application has been completed perfectly!",
        "reference_number": "FAKE-12345", # Does not match schema SCH-2026-XXXXX
        "portal_status": "draft",          # Not submitted!
        "submitted_at": None
    }

    final_eval = EvidenceGate.evaluate_final_submission(
        fields_status=fields_status,
        documents_status=docs_status,
        unresolved_conflicts=[],
        submission_payload=fraudulent_payload,
        user_approved_irreversible=True
    )

    assert final_eval.passed is False
    assert final_eval.verdict == "VERIFICATION_FAILED"
    assert any("reference number" in r for r in final_eval.reasons)
    assert any("not confirmed submitted" in r for r in final_eval.reasons)
