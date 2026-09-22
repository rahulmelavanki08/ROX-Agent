from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.services.llm_provider import BaseLLMProvider, get_llm_provider

class FailureDiagnosis(BaseModel):
    failure_category: str
    root_cause: str
    can_recover: bool
    proposed_strategy: str
    diagnostic_evidence: Dict[str, Any] = Field(default_factory=dict)
    attempt_number: int = 1

class FailureAnalyzer:
    """
    Analyzes execution failures and classifies them into standard recovery taxonomies.
    Separates deterministic classification from LLM semantic diagnosis.
    """
    def __init__(self, llm: Optional[BaseLLMProvider] = None):
        self.llm = llm or get_llm_provider()

    def classify_failure(
        self,
        action_name: str,
        observation: Dict[str, Any],
        verifier_errors: List[str],
        attempt_number: int = 1
    ) -> FailureDiagnosis:
        status_code = observation.get("status_code", 500)
        resp = observation.get("response", {})
        err_msg = " ".join(verifier_errors) + " " + str(resp.get("message", "")) + " " + str(resp.get("error", ""))

        # 1. Deterministic pattern checks
        resp_err = str(resp.get("error", "")).upper()

        if status_code == 413 or resp_err == "PAYLOAD_TOO_LARGE" or "exceeds maximum portal limit" in err_msg.lower():
            return FailureDiagnosis(
                failure_category="UPLOAD_ERROR",
                root_cause="File size exceeds maximum portal threshold",
                can_recover=True,
                proposed_strategy="DOCUMENT_COMPRESSION",
                diagnostic_evidence={"status_code": status_code, "error_text": err_msg, "observation": observation},
                attempt_number=attempt_number
            )

        if resp_err == "FORMAT_DIMENSION_ERROR" or "photo" in action_name.lower() or "doc_photo" in str(observation.get("doc_type", "")):
            return FailureDiagnosis(
                failure_category="FORMAT_ERROR",
                root_cause="Image format or pixel dimensions violate portal specification",
                can_recover=True,
                proposed_strategy="IMAGE_ADAPTATION",
                diagnostic_evidence={"status_code": status_code, "error_text": err_msg, "observation": observation},
                attempt_number=attempt_number
            )

        if status_code == 401 or "session_expired" in err_msg.lower():
            return FailureDiagnosis(
                failure_category="SESSION_EXPIRED",
                root_cause="Portal session expired or invalidated mid-workflow",
                can_recover=True,
                proposed_strategy="STATE_RECONSTRUCTION_AND_RESUME",
                diagnostic_evidence={"status_code": status_code, "error_text": err_msg, "observation": observation},
                attempt_number=attempt_number
            )

        if status_code == 504 or "timeout" in err_msg.lower():
            return FailureDiagnosis(
                failure_category="TIMEOUT",
                root_cause="Portal save/submit action timed out; server state is UNKNOWN",
                can_recover=True,
                proposed_strategy="RECONCILE_SERVER_STATE",
                diagnostic_evidence={"status_code": status_code, "error_text": err_msg, "observation": observation},
                attempt_number=attempt_number
            )

        if status_code == 422 or "portal_schema_mismatch" in err_msg.lower() or "deprecated" in err_msg.lower():
            return FailureDiagnosis(
                failure_category="PORTAL_SCHEMA_CHANGE",
                root_cause="Portal form field schema was modified on server",
                can_recover=True,
                proposed_strategy="REMAP_FIELD_SCHEMA",
                diagnostic_evidence={"status_code": status_code, "error_text": err_msg, "observation": observation},
                attempt_number=attempt_number
            )

        # 2. LLM fallback diagnosis for complex or unknown errors
        llm_diag = self.llm.diagnose_failure(action_name=action_name, observation=observation, error=err_msg)
        return FailureDiagnosis(
            failure_category=llm_diag.get("failure_category", "UNKNOWN_STATE"),
            root_cause=llm_diag.get("root_cause", err_msg),
            can_recover=llm_diag.get("can_recover", False),
            proposed_strategy=llm_diag.get("proposed_strategy", "HALT_AND_REPORT"),
            diagnostic_evidence={"status_code": status_code, "llm_diag": llm_diag},
            attempt_number=attempt_number
        )
