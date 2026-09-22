import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from app.services.text_extractor import extract_fields_from_raw_text

client = TestClient(app)

def test_extract_from_custom_user_text():
    custom_doc = """
    GOVERNMENT OF INDIA
    NATIONAL CITIZEN IDENTIFICATION
    Applicant Name: Ananya Sharma
    DOB: 22/04/2005
    Gender: Female
    Social Category: OBC
    College: RV College of Engineering
    Roll Number: 1RV22CS010
    10th Standard Aggregate: 94.2%
    12th / Pre-University Aggregate: 91.8%
    Certified Annual Family Income: Rs. 1,80,000 /-
    Bank: HDFC Bank
    Account Number: 50100234123456
    IFSC Code: HDFC0001234
    Aadhaar Number: 4920 3819 4821
    """
    fields = extract_fields_from_raw_text(custom_doc, "my_custom_id.pdf", "doc_aadhaar")
    f_map = {f["field"]: f["value"] for f in fields}
    
    assert f_map["full_name"] == "Ananya Sharma"
    assert f_map["date_of_birth"] == "22/04/2005"
    assert f_map["gender"] == "Female"
    assert f_map["category"] == "Obc"
    assert f_map["roll_number"] == "1RV22CS010"
    assert f_map["annual_family_income"] == "180000"
    assert f_map["bank_account_number"] == "50100234123456"
    assert f_map["ifsc_code"] == "HDFC0001234"

def test_upload_custom_named_file_with_doc_type():
    init_res = client.post("/api/v1/applications/init", json={"application_type": "scholarship_sbi"})
    app_id = init_res.json()["application_id"]

    # Upload custom named file with doc_type="doc_aadhaar"
    dummy_content = b"%PDF-1.4 dummy aadhaar pdf with Name: Ananya Sharma and DOB: 22/04/2005"
    files = {"file": ("my_scan_001.pdf", dummy_content, "application/pdf")}
    data = {"doc_type": "doc_aadhaar"}
    upload_res = client.post(f"/api/v1/applications/{app_id}/upload", files=files, data=data)
    assert upload_res.status_code == 200
    assert upload_res.json()["doc_type"] == "doc_aadhaar"

    # Check documents endpoint
    docs_res = client.get(f"/api/v1/applications/{app_id}/documents")
    assert docs_res.status_code == 200
    doc = docs_res.json()["documents"][0]
    assert doc["file_name"] == "my_scan_001.pdf"
    assert doc["doc_type"] == "doc_aadhaar"

    # Update field directly
    up_res = client.post(f"/api/v1/applications/{app_id}/update-field", json={
        "field_id": "full_name",
        "value": "Ananya Sharma"
    })
    assert up_res.status_code == 200
    assert up_res.json()["value"] == "Ananya Sharma"
