import os
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from app.portal.mock_portal import mock_portal, MockScholarshipPortal
from app.services.document_engine import DocumentEngine

class MockScholarshipPortalAdapter:
    """
    Adapter implementing deterministic portal interactions.
    Provides uniform observation objects containing status codes,
    headers, bodies, and DOM simulation for the Evidence Gate.
    """
    def __init__(self, portal: Optional[MockScholarshipPortal] = None):
        self.portal = portal or mock_portal

    def start_session(self) -> str:
        session = self.portal.create_session()
        return session.session_id

    def discover_fields(self) -> Dict[str, Any]:
        return {
            "portal_name": "National Scholarship Portal 2026",
            "steps": ["Personal Details", "Academic Details", "Financial Details", "Document Uploads", "Review & Submit"],
            "url": "http://localhost:8000/portal"
        }

    def fill_step(self, session_id: str, step_name: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        res = self.portal.save_step(session_id, step_name, form_data)
        return {
            "operation": "fill_step",
            "step_name": step_name,
            "session_id": session_id,
            "data_submitted": form_data,
            "response": res,
            "status_code": res.get("status_code", 500),
            "success": res.get("success", False),
            "error": res.get("error"),
            "observed_at": time.time()
        }

    def upload_document(self, session_id: str, doc_type: str, file_path: str) -> Dict[str, Any]:
        if not file_path:
            return {
                "operation": "upload_document",
                "doc_type": doc_type,
                "success": False,
                "status_code": 400,
                "error": "FILE_PATH_EMPTY",
                "message": f"No file provided for {doc_type}"
            }
        p = Path(file_path)
        if not p.exists():
            return {
                "operation": "upload_document",
                "doc_type": doc_type,
                "success": False,
                "status_code": 404,
                "error": "FILE_NOT_FOUND",
                "message": f"Local file {file_path} not found on disk"
            }

        size_kb = os.path.getsize(file_path) / 1024.0
        ext = p.suffix.lower()
        mime_type = "application/pdf" if ext == ".pdf" else "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
        
        dims = None
        if ext in [".jpg", ".jpeg", ".png"]:
            stat = DocumentEngine.inspect_image(file_path)
            dims = (stat["width"], stat["height"])

        res = self.portal.upload_document(
            session_id=session_id,
            doc_type=doc_type,
            filename=p.name,
            file_size_kb=size_kb,
            mime_type=mime_type,
            dimensions=dims
        )

        return {
            "operation": "upload_document",
            "doc_type": doc_type,
            "file_name": p.name,
            "file_size_kb": round(size_kb, 2),
            "mime_type": mime_type,
            "dimensions": dims,
            "response": res,
            "status_code": res.get("status_code", 500),
            "success": res.get("success", False),
            "error": res.get("error"),
            "observed_at": time.time()
        }

    def get_application_state(self, session_id: str) -> Dict[str, Any]:
        return self.portal.query_portal_state(session_id)

    def submit_application(self, session_id: str) -> Dict[str, Any]:
        res = self.portal.submit_application(session_id)
        return {
            "operation": "submit_application",
            "session_id": session_id,
            "response": res,
            "status_code": res.get("status_code", 500),
            "success": res.get("success", False),
            "reference_number": res.get("reference_number"),
            "receipt": res.get("receipt"),
            "observed_at": time.time()
        }

    def verify_submission(self, session_id: str, reference_number: str) -> Dict[str, Any]:
        state = self.portal.query_portal_state(session_id)
        portal_ref = state.get("reference_number")
        is_submitted = state.get("submitted", False)
        
        matches = (portal_ref == reference_number) and is_submitted
        return {
            "verified": matches,
            "portal_status": "Submitted" if is_submitted else "Not Submitted",
            "reference_number": portal_ref,
            "state_snapshot": state
        }
