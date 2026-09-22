import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.core.state_machine import ApplicationState

client = TestClient(app)

def test_full_rox_e2e_evidence_gated_workflow():
    # 1. Initialize application
    init_res = client.post("/api/v1/applications/init", json={
        "portal_url": "http://localhost:8000/portal",
        "user_goal": "Complete scholarship application using uploaded documents."
    })
    assert init_res.status_code == 200
    app_data = init_res.json()
    app_id = app_data["application_id"]
    assert app_data["state"] == "NOT_STARTED"

    # 2. Load demo dataset (sample documents)
    load_res = client.post(f"/api/v1/sample-docs/load?application_id={app_id}")
    assert load_res.status_code == 200
    assert len(load_res.json()["documents"]) >= 4

    # 3. Analyze application (Triggers requirement parsing, document ingestion, and DOB conflict detection!)
    analyze_res = client.post(f"/api/v1/applications/{app_id}/analyze")
    assert analyze_res.status_code == 200
    an_data = analyze_res.json()
    assert an_data["state"] == "BLOCKED"
    assert an_data["mapping"]["unresolved_conflicts_count"] == 1
    conflict = an_data["mapping"]["conflicts"][0]
    assert conflict["field_id"] == "date_of_birth"

    # 4. Resolve conflict (User resolves DOB to 14/05/2007)
    resolve_res = client.post(f"/api/v1/applications/{app_id}/resolve-conflict", json={
        "field_id": "date_of_birth",
        "chosen_value": "14/05/2007",
        "source_reference": "aadhaar.pdf"
    })
    assert resolve_res.status_code == 200
    assert resolve_res.json()["remaining_conflicts"] == 0
    assert resolve_res.json()["state"] == "AWAITING_PLAN_APPROVAL"

    # 5. Approve execution plan
    plan_res = client.post(f"/api/v1/applications/{app_id}/approve-plan", json={"approved": True})
    assert plan_res.status_code == 200
    assert plan_res.json()["state"] == "PLANNED"

    # 6. Run Zero-Trust Execution Loop (Triggers Failures & Self-Healing Recoveries!)
    exec_res = client.post(f"/api/v1/applications/{app_id}/execute")
    assert exec_res.status_code == 200
    ex_data = exec_res.json()
    assert ex_data["state"] == "READY_FOR_REVIEW"
    actions = ex_data["actions_executed"]
    assert len(actions) == 7

    # Verify that Income Certificate upload failed on attempt 1 and recovered on attempt 2!
    income_act = next(a for a in actions if a["action_id"] == "ACT_006_UPLOAD_INCOME_CERT")
    assert income_act["status"] == "VERIFIED"
    assert income_act["attempt"] == 2  # Recovered via compression!

    # Verify that Photograph upload failed on attempt 1 (format/dimension) and recovered on attempt 2!
    photo_act = next(a for a in actions if a["action_id"] == "ACT_007_UPLOAD_PHOTO")
    assert photo_act["status"] == "VERIFIED"
    assert photo_act["attempt"] == 2   # Recovered via image adaptation!

    # 7. Check Review Data
    rev_res = client.get(f"/api/v1/applications/{app_id}/review-data")
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert len(rev_data["review_fields"]) >= 10
    assert all(d["verified"] for d in rev_data["documents_status"])

    # 8. Irreversible Action Guard: Attempt submit without approval -> MUST BE FORBIDDEN (403)!
    unauthorized_submit = client.post(f"/api/v1/applications/{app_id}/submit")
    assert unauthorized_submit.status_code == 403

    # 9. Grant human authorization
    auth_res = client.post(f"/api/v1/applications/{app_id}/approve-submission", json={"user_confirmed": True})
    assert auth_res.status_code == 200

    # 10. Execute Final Submission & Evidence Gate Verification
    submit_res = client.post(f"/api/v1/applications/{app_id}/submit")
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    assert sub_data["status"] == "SUCCESS"
    assert sub_data["state"] == "VERIFIED_SUCCESS"
    assert sub_data["gate_decision"]["passed"] is True
    assert "reference_number" in sub_data["submission_details"]
    assert sub_data["submission_details"]["reference_number"].startswith("SCH-2026-")

    # 11. Verify Proof Ledger integrity
    ledger_res = client.get(f"/api/v1/applications/{app_id}/ledger")
    assert ledger_res.status_code == 200
    entries = ledger_res.json()["entries"]
    assert len(entries) >= 10
    # Verify hash chain exists
    assert all("entry_hash" in e and len(e["entry_hash"]) == 64 for e in entries)
    print("ALL 11 E2E STAGES VERIFIED!")
