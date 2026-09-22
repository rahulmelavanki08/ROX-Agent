import time
import uuid
import hashlib
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PortalSession(BaseModel):
    session_id: str
    created_at: float = Field(default_factory=time.time)
    last_active: float = Field(default_factory=time.time)
    is_expired: bool = False
    draft_data: Dict[str, Any] = Field(default_factory=dict)
    uploaded_files: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    current_step: int = 1
    submitted: bool = False
    reference_number: Optional[str] = None
    receipt: Optional[Dict[str, Any]] = None

class FailureFlags(BaseModel):
    reject_oversized_income: bool = True       # Rejects PDF > 2048 KB
    strict_photo_requirements: bool = True     # Requires JPG, 200x230, < 100 KB
    simulate_session_expire: bool = False      # Forces 401 Session Expired
    simulate_save_timeout: bool = False        # Forces timeout / unknown state
    simulate_schema_change: bool = False       # Renames annual_family_income to annual_income_revised
    simulate_portal_error: bool = False        # Forces 500 server error

class MockScholarshipPortal:
    """
    Realistic multi-step government scholarship portal backend.
    Enforces authentic constraints, session states, file size limits,
    and supports dynamic failure injection for hackathon demonstration.
    """
    def __init__(self):
        self.sessions: Dict[str, PortalSession] = {}
        self.flags = FailureFlags()
        self.submissions_db: Dict[str, Dict[str, Any]] = {}

    def create_session(self) -> PortalSession:
        sid = f"sess_{uuid.uuid4().hex[:12]}"
        session = PortalSession(session_id=sid)
        self.sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> Optional[PortalSession]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        if self.flags.simulate_session_expire or session.is_expired:
            session.is_expired = True
            return None
        session.last_active = time.time()
        return session

    def save_step(self, session_id: str, step_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.flags.simulate_session_expire:
            return {"success": False, "status_code": 401, "error": "SESSION_EXPIRED", "message": "Portal session has timed out due to inactivity."}

        if self.flags.simulate_save_timeout:
            # Clear flag after firing once to allow recovery demonstration
            self.flags.simulate_save_timeout = False
            # Data IS saved internally, but response returns timeout (classic unknown state problem!)
            session = self.sessions.get(session_id)
            if session:
                session.draft_data.update(data)
            return {"success": False, "status_code": 504, "error": "GATEWAY_TIMEOUT", "message": "Gateway timeout occurred while saving application draft."}

        session = self.get_session(session_id)
        if not session:
            return {"success": False, "status_code": 401, "error": "SESSION_EXPIRED", "message": "Portal session expired or invalid."}

        # Schema change simulation
        if self.flags.simulate_schema_change and "annual_family_income" in data:
            return {
                "success": False,
                "status_code": 422,
                "error": "PORTAL_SCHEMA_MISMATCH",
                "message": "Field 'annual_family_income' has been deprecated by portal update. Expected: 'annual_income_revised'"
            }

        session.draft_data.update(data)
        return {
            "success": True,
            "status_code": 200,
            "session_id": session_id,
            "step_saved": step_name,
            "persisted_fields": list(session.draft_data.keys()),
            "last_updated": time.time()
        }

    def upload_document(
        self,
        session_id: str,
        doc_type: str,
        filename: str,
        file_size_kb: float,
        mime_type: str,
        dimensions: Optional[tuple] = None
    ) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "status_code": 401, "error": "SESSION_EXPIRED", "message": "Portal session expired. Cannot accept file upload."}

        # Failure Injection 1: Oversized Income Certificate
        if doc_type in ["income_certificate", "doc_income_cert"]:
            limit_kb = 2048.0
            if self.flags.reject_oversized_income and file_size_kb > limit_kb:
                return {
                    "success": False,
                    "status_code": 413,
                    "error": "PAYLOAD_TOO_LARGE",
                    "message": f"Upload failed: File size ({file_size_kb:.1f} KB) exceeds maximum portal limit of {limit_kb:.0f} KB.",
                    "constraint": {"max_kb": limit_kb, "observed_kb": file_size_kb}
                }

        # Failure Injection 2: Photo format and dimension check
        if doc_type in ["applicant_photo", "doc_photo"]:
            if self.flags.strict_photo_requirements:
                is_jpg = "jpeg" in mime_type.lower() or "jpg" in mime_type.lower() or filename.lower().endswith((".jpg", ".jpeg"))
                is_dim_exact = dimensions == (200, 230)
                is_size_ok = file_size_kb <= 100.0

                if not is_jpg or not is_dim_exact or not is_size_ok:
                    details = []
                    if not is_jpg:
                        details.append(f"Invalid format '{mime_type}' (Must be JPG/JPEG)")
                    if not is_dim_exact:
                        details.append(f"Dimensions {dimensions} do not match strict requirement 200x230 pixels")
                    if not is_size_ok:
                        details.append(f"File size {file_size_kb:.1f} KB exceeds 100 KB limit")
                    
                    return {
                        "success": False,
                        "status_code": 400,
                        "error": "FORMAT_DIMENSION_ERROR",
                        "message": "Upload rejected: " + "; ".join(details),
                        "required": {"format": "JPEG", "dimensions": [200, 230], "max_kb": 100},
                        "observed": {"format": mime_type, "dimensions": dimensions, "size_kb": file_size_kb}
                    }

        # Accepted upload
        doc_record = {
            "doc_type": doc_type,
            "filename": filename,
            "size_kb": file_size_kb,
            "mime_type": mime_type,
            "dimensions": dimensions,
            "uploaded_at": time.time(),
            "checksum": hashlib.md5(f"{filename}_{file_size_kb}".encode()).hexdigest()
        }
        session.uploaded_files[doc_type] = doc_record
        return {
            "success": True,
            "status_code": 200,
            "message": f"Document '{doc_type}' successfully uploaded and verified by portal.",
            "doc_record": doc_record
        }

    def query_portal_state(self, session_id: str) -> Dict[str, Any]:
        session = self.sessions.get(session_id)
        if not session:
            return {"exists": False, "status": "UNKNOWN", "message": "Session not found in portal database."}

        return {
            "exists": True,
            "session_id": session_id,
            "is_expired": session.is_expired,
            "persisted_fields": list(session.draft_data.keys()),
            "draft_values": session.draft_data,
            "uploaded_documents": list(session.uploaded_files.keys()),
            "submitted": session.submitted,
            "reference_number": session.reference_number,
            "last_active": session.last_active
        }

    def submit_application(self, session_id: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            return {"success": False, "status_code": 401, "error": "SESSION_EXPIRED", "message": "Session expired before submission."}

        # Check required fields
        required_fields = ["full_name", "date_of_birth", "gender", "institution_name", "annual_family_income", "bank_account_number"]
        missing = [f for f in required_fields if f not in session.draft_data]
        if missing:
            return {
                "success": False,
                "status_code": 400,
                "error": "MANDATORY_FIELDS_MISSING",
                "message": f"Cannot submit: Mandatory fields missing: {missing}"
            }

        # Check required documents
        # At minimum, primary identity document (doc_aadhaar) is required.
        required_docs = ["doc_aadhaar"]
        missing_docs = [d for d in required_docs if d not in session.uploaded_files]
        if missing_docs:
            return {
                "success": False,
                "status_code": 400,
                "error": "MANDATORY_DOCUMENTS_MISSING",
                "message": f"Cannot submit: Missing required uploads: {missing_docs}"
            }

        # Generate official submission receipt
        ref_num = f"SCH-2026-{random.randint(10000, 99999)}"
        timestamp = time.time()
        receipt_data = {
            "application_id": session_id,
            "reference_number": ref_num,
            "portal_status": "Submitted",
            "submitted_at": timestamp,
            "candidate_name": session.draft_data.get("full_name"),
            "category": session.draft_data.get("category", "General"),
            "income": session.draft_data.get("annual_family_income"),
            "verified_documents_count": len(session.uploaded_files),
            "receipt_hash": hashlib.sha256(f"{ref_num}_{session_id}_{timestamp}".encode()).hexdigest()
        }

        session.submitted = True
        session.reference_number = ref_num
        session.receipt = receipt_data
        self.submissions_db[ref_num] = receipt_data

        return {
            "success": True,
            "status_code": 200,
            "message": "Application submitted and verified successfully.",
            "reference_number": ref_num,
            "receipt": receipt_data
        }

mock_portal = MockScholarshipPortal()
