import os
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.services.document_engine import DocumentEngine

class VerifierAgent:
    """
    DETERMINISTIC VERIFICATION AGENT.
    Performs independent inspection of files, DOM states, HTTP responses,
    and server state without relying on LLM self-assessment.
    """

    @staticmethod
    def verify_field_action(observation: Dict[str, Any], expected_fields: List[str]) -> Tuple[bool, Dict[str, Any], List[str]]:
        errors = []
        status_code = observation.get("status_code", 500)
        success = observation.get("success", False)
        resp = observation.get("response", {})
        persisted = resp.get("persisted_fields", [])

        if status_code != 200:
            errors.append(f"HTTP status was {status_code}, expected 200")
        if not success:
            errors.append(f"Portal returned failure: {resp.get('error')} - {resp.get('message')}")

        missing_fields = [f for f in expected_fields if f not in persisted]
        if missing_fields:
            errors.append(f"Fields not persisted on portal: {missing_fields}")

        evidence = {
            "http_status": status_code,
            "portal_confirmed_fields": persisted,
            "server_timestamp": resp.get("last_updated"),
            "verified_by": "VerifierAgent.verify_field_action"
        }
        return (len(errors) == 0, evidence, errors)

    @staticmethod
    def verify_upload_action(
        observation: Dict[str, Any],
        file_path: str,
        expected_doc_type: str,
        max_kb: float,
        expected_dimensions: Optional[Tuple[int, int]] = None
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        errors = []
        status_code = observation.get("status_code", 500)
        success = observation.get("success", False)
        resp = observation.get("response", {})

        if status_code != 200:
            errors.append(f"Portal upload rejected with HTTP {status_code}: {resp.get('message')}")
        if not success:
            errors.append(f"Portal upload failed: {resp.get('error')}")

        # Independent on-disk verification
        disk_audit = DocumentEngine.verify_document_contract(
            file_path=file_path,
            expected_extension=Path(file_path).suffix,
            max_size_kb=max_kb,
            expected_dimensions=expected_dimensions
        )
        if not disk_audit.get("valid", False):
            errors.append(f"On-disk file verification failed: {disk_audit}")

        evidence = {
            "portal_accepted": success and status_code == 200,
            "portal_checksum": resp.get("doc_record", {}).get("checksum"),
            "on_disk_size_kb": disk_audit.get("file_size_kb"),
            "on_disk_dimensions": disk_audit.get("dimensions"),
            "verified_by": "VerifierAgent.verify_upload_action"
        }
        return (len(errors) == 0, evidence, errors)

    @staticmethod
    def verify_final_submission(observation: Dict[str, Any], expected_name: str) -> Tuple[bool, Dict[str, Any], List[str]]:
        errors = []
        status_code = observation.get("status_code", 500)
        success = observation.get("success", False)
        receipt = observation.get("receipt") or {}
        ref_num = receipt.get("reference_number", "")

        if status_code != 200 or not success:
            errors.append(f"Submission failed with status {status_code}: {observation.get('error')}")

        if not ref_num or not re.match(r"^SCH-2026-\d{4,6}$", str(ref_num)):
            errors.append(f"Generated reference number '{ref_num}' does not match schema SCH-2026-XXXXX")

        status = str(receipt.get("portal_status", "")).lower()
        if status != "submitted":
            errors.append(f"Portal status is '{status}', expected 'submitted'")

        # Verify receipt integrity hash
        receipt_hash = receipt.get("receipt_hash")
        app_id = receipt.get("application_id")
        ts = receipt.get("submitted_at")
        expected_hash = hashlib.sha256(f"{ref_num}_{app_id}_{ts}".encode()).hexdigest()
        if receipt_hash != expected_hash:
            errors.append("Cryptographic receipt hash verification failed")

        evidence = {
            "reference_number": ref_num,
            "portal_status": receipt.get("portal_status"),
            "submitted_at": receipt.get("submitted_at"),
            "receipt_hash": receipt_hash,
            "hash_verified": receipt_hash == expected_hash,
            "candidate_name": receipt.get("candidate_name"),
            "verified_by": "VerifierAgent.verify_final_submission"
        }
        return (len(errors) == 0, evidence, errors)
