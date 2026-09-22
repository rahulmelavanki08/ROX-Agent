import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app

client = TestClient(app)

def test_application_types_catalog():
    res = client.get("/api/v1/application-types")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    types = data["types"]
    assert len(types) >= 3
    type_ids = [t["id"] for t in types]
    assert "scholarship_sbi" in type_ids
    assert "hostel_post_matric" in type_ids
    assert "certificate_income_caste" in type_ids

def test_file_issues_detection_and_adaptation():
    # 1. Init
    init_res = client.post("/api/v1/applications/init", json={
        "application_type": "scholarship_sbi",
        "portal_url": "http://localhost:8000/portal"
    })
    assert init_res.status_code == 200
    app_id = init_res.json()["application_id"]

    # 2. Load demo documents
    load_res = client.post(f"/api/v1/sample-docs/load?application_id={app_id}")
    assert load_res.status_code == 200

    # 3. Check documents endpoint
    docs_res = client.get(f"/api/v1/applications/{app_id}/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()["documents"]
    assert len(docs) >= 4

    # 4. Analyze to detect file issues
    analyze_res = client.post(f"/api/v1/applications/{app_id}/analyze")
    assert analyze_res.status_code == 200
    an_data = analyze_res.json()
    file_issues = an_data.get("file_issues", [])
    assert len(file_issues) >= 2
    issue_types = [fi["issue_type"] for fi in file_issues]
    assert "OVERSIZED_FILE" in issue_types
    assert "UNSUPPORTED_FORMAT_OR_DIMENSIONS" in issue_types

    # 5. Adapt oversized file (compress_pdf)
    oversized = next(fi for fi in file_issues if fi["issue_type"] == "OVERSIZED_FILE")
    adapt_pdf_res = client.post(f"/api/v1/applications/{app_id}/adapt-file", json={
        "file_name": oversized["file_name"],
        "action": "compress_pdf"
    })
    assert adapt_pdf_res.status_code == 200
    pdf_res_data = adapt_pdf_res.json()
    assert pdf_res_data["status"] == "SUCCESS"
    assert pdf_res_data["verified"] is True
    assert pdf_res_data["final_size_kb"] < 2048

    # 6. Adapt image file (convert_image)
    image_issue = next(fi for fi in file_issues if fi["issue_type"] == "UNSUPPORTED_FORMAT_OR_DIMENSIONS")
    adapt_img_res = client.post(f"/api/v1/applications/{app_id}/adapt-file", json={
        "file_name": image_issue["file_name"],
        "action": "convert_image"
    })
    assert adapt_img_res.status_code == 200
    img_res_data = adapt_img_res.json()
    assert img_res_data["status"] == "SUCCESS"
    assert img_res_data["verified"] is True
    assert img_res_data["dimensions"]["width"] == 200
    assert img_res_data["dimensions"]["height"] == 230
    assert img_res_data["final_size_kb"] <= 100

def test_auto_adapt_all_image_to_pdf_and_compress():
    # 1. Init
    init_res = client.post("/api/v1/applications/init", json={"application_type": "scholarship_sbi"})
    app_id = init_res.json()["application_id"]

    # 2. Upload an image as doc_aadhaar and an oversized PDF as doc_income_cert
    sample_img = Path("backend/storage/uploads/APP_DFD87CF1/adharcard.jpeg")
    sample_pdf = Path("backend/sample_docs/income_certificate.pdf")

    with open(sample_img, "rb") as f_img:
        client.post(f"/api/v1/applications/{app_id}/upload", files={"file": ("my_aadhaar.jpeg", f_img, "image/jpeg")}, data={"doc_type": "doc_aadhaar"})
    with open(sample_pdf, "rb") as f_pdf:
        client.post(f"/api/v1/applications/{app_id}/upload", files={"file": ("my_income.pdf", f_pdf, "application/pdf")}, data={"doc_type": "doc_income_cert"})

    # 3. Analyze -> file issues detected
    an_res = client.post(f"/api/v1/applications/{app_id}/analyze")
    assert an_res.status_code == 200
    issues = an_res.json()["file_issues"]
    assert len(issues) >= 2
    actions_needed = [i["action_required"] for i in issues]
    assert "convert_to_pdf" in actions_needed
    assert "compress_pdf" in actions_needed

    # 4. Zero-touch auto-adapt-all without manual clicking
    auto_res = client.post(f"/api/v1/applications/{app_id}/auto-adapt-all")
    assert auto_res.status_code == 200
    auto_data = auto_res.json()
    assert auto_data["status"] == "SUCCESS"
    assert auto_data["adapted_count"] >= 2
    assert len(auto_data["remaining_issues"]) == 0

    # 5. Check converted file is valid PDF
    pdf_converted = next(r for r in auto_data["results"] if r["action"] == "convert_to_pdf")
    assert pdf_converted["adapted_file"].endswith(".pdf")
    assert pdf_converted["verified"] is True
