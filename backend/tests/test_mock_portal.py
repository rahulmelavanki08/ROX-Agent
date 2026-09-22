import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.portal.mock_portal import MockScholarshipPortal

def test_portal_session_and_step_saving():
    portal = MockScholarshipPortal()
    sess = portal.create_session()
    assert sess.session_id.startswith("sess_")

    res = portal.save_step(sess.session_id, "Personal Details", {"full_name": "Rahul Melavanki"})
    assert res["success"] is True
    assert "full_name" in res["persisted_fields"]

def test_portal_upload_oversized_failure():
    portal = MockScholarshipPortal()
    sess = portal.create_session()

    # Attempt to upload 4500 KB income cert
    res = portal.upload_document(
        session_id=sess.session_id,
        doc_type="income_certificate",
        filename="income.pdf",
        file_size_kb=4500.0,
        mime_type="application/pdf"
    )
    assert res["success"] is False
    assert res["status_code"] == 413
    assert "exceeds maximum portal limit" in res["message"]

def test_portal_upload_strict_photo_failure():
    portal = MockScholarshipPortal()
    sess = portal.create_session()

    # Attempt to upload PNG with wrong dimensions (1600x1200)
    res = portal.upload_document(
        session_id=sess.session_id,
        doc_type="applicant_photo",
        filename="photo.png",
        file_size_kb=150.0,
        mime_type="image/png",
        dimensions=(1600, 1200)
    )
    assert res["success"] is False
    assert res["status_code"] == 400
    assert "FORMAT_DIMENSION_ERROR" in res["error"]

def test_portal_session_expiration_hook():
    portal = MockScholarshipPortal()
    sess = portal.create_session()
    
    # Inject expiration
    portal.flags.simulate_session_expire = True
    res = portal.save_step(sess.session_id, "Personal Details", {"name": "test"})
    assert res["success"] is False
    assert res["status_code"] == 401
    portal.flags.simulate_session_expire = False

def test_portal_save_timeout_unknown_state():
    portal = MockScholarshipPortal()
    sess = portal.create_session()
    
    # Inject save timeout
    portal.flags.simulate_save_timeout = True
    res = portal.save_step(sess.session_id, "Personal Details", {"name": "test"})
    assert res["success"] is False
    assert res["status_code"] == 504

    # Verify that query_portal_state reveals the true server state
    state = portal.query_portal_state(sess.session_id)
    assert "name" in state["persisted_fields"]
