import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.conflict_detector import ConflictDetector

def test_dob_conflict_detection():
    # Simulate extraction where Aadhaar and Marksheet have different DOBs
    extractions = {
        "date_of_birth": [
            {"value": "14/05/2007", "source_file": "aadhaar.pdf", "source_page": 1, "confidence": 0.99},
            {"value": "15/05/2007", "source_file": "marksheet.pdf", "source_page": 1, "confidence": 0.98}
        ],
        "full_name": [
            {"value": "Rahul Melavanki", "source_file": "aadhaar.pdf", "source_page": 1, "confidence": 0.99},
            {"value": "Rahul Melavanki", "source_file": "marksheet.pdf", "source_page": 1, "confidence": 0.99}
        ]
    }

    conflicts = ConflictDetector.detect_conflicts(extractions)
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.field_id == "date_of_birth"
    assert len(c.candidates) == 2
    assert "14/05/2007" in [cand.value for cand in c.candidates]
    assert "15/05/2007" in [cand.value for cand in c.candidates]

def test_no_conflict_when_values_match():
    extractions = {
        "full_name": [
            {"value": "Kumar. M Vinayaka", "source_file": "income_cert.pdf"},
            {"value": "M Vinayaka", "source_file": "aadhaar.pdf"}
        ]
    }
    conflicts = ConflictDetector.detect_conflicts(extractions)
    assert len(conflicts) == 0

def test_cross_document_two_different_people_mismatch():
    # User uploads Aadhaar card of Person A and Marksheet of Person B
    extractions = {
        "full_name": [
            {"value": "M Vinayaka", "source_file": "adharcard.jpeg", "evidence_text": "M Vinayaka cto"},
            {"value": "M Veeresh", "source_file": "marksheet.jpeg", "evidence_text": "UNOLISH M VEERESH M PRAKASH"}
        ],
        "date_of_birth": [
            {"value": "24/08/2007", "source_file": "adharcard.jpeg", "evidence_text": "DOB: 24/08/2007"},
            {"value": "18/08/2009", "source_file": "marksheet.jpeg", "evidence_text": "EIGHTEENTH.AUGUST. TWO THOUSAND NINE"}
        ]
    }

    conflicts = ConflictDetector.detect_conflicts(extractions)
    # Both full_name and date_of_birth must be flagged as critical conflicts
    assert len(conflicts) == 2
    c_map = {c.field_id: c for c in conflicts}

    assert "full_name" in c_map
    assert "date_of_birth" in c_map
    assert "Identity Mismatch detected" in c_map["full_name"].blocking_reason
    assert "M Vinayaka" in [cand.value for cand in c_map["full_name"].candidates]
    assert "M Veeresh" in [cand.value for cand in c_map["full_name"].candidates]
    assert "24/08/2007" in [cand.value for cand in c_map["date_of_birth"].candidates]
    assert "18/08/2009" in [cand.value for cand in c_map["date_of_birth"].candidates]

