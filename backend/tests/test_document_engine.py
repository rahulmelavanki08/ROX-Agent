import pytest
import os
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.document_engine import DocumentEngine
from app.core.config import settings

def test_pdf_extraction():
    aadhaar_path = str(settings.SAMPLE_DOCS_DIR / "aadhaar.pdf")
    res = DocumentEngine.extract_text_from_pdf(aadhaar_path)
    assert res["page_count"] >= 1
    assert "Rahul Melavanki" in res["full_text"]
    assert "14/05/2007" in res["full_text"]

def test_image_inspection():
    photo_path = str(settings.SAMPLE_DOCS_DIR / "photo.png")
    stat = DocumentEngine.inspect_image(photo_path)
    assert stat["format"] == "PNG"
    assert stat["width"] == 1600
    assert stat["height"] == 1200

def test_image_adaptation_to_portal_contract():
    photo_path = str(settings.SAMPLE_DOCS_DIR / "photo.png")
    adapted_path = str(settings.STORAGE_DIR / "test_adapted_photo.jpg")
    
    res = DocumentEngine.adapt_image(
        input_path=photo_path,
        output_path=adapted_path,
        target_format="JPEG",
        target_dimensions=(200, 230),
        max_size_kb=100
    )
    assert res["verified"] is True
    assert res["dimensions"]["width"] == 200
    assert res["dimensions"]["height"] == 230
    assert res["file_size_kb"] <= 100
    assert res["output_format"] == "JPEG"

def test_pdf_compression():
    income_path = str(settings.SAMPLE_DOCS_DIR / "income_certificate.pdf")
    compressed_path = str(settings.STORAGE_DIR / "test_compressed_income.pdf")
    
    res = DocumentEngine.compress_pdf(
        input_path=income_path,
        output_path=compressed_path,
        target_kb=2048
    )
    assert res["verified"] is True
    assert res["final_size_kb"] <= 2048
