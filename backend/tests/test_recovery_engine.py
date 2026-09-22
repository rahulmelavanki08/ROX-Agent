import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.agents.failure_analyzer import FailureDiagnosis
from app.agents.recovery_agent import RecoveryAgent
from app.services.portal_adapter import MockScholarshipPortalAdapter

def test_bounded_recovery_exceeded():
    adapter = MockScholarshipPortalAdapter()
    agent = RecoveryAgent(portal_adapter=adapter, max_attempts=3)

    diagnosis = FailureDiagnosis(
        failure_category="UPLOAD_ERROR",
        root_cause="Oversized",
        can_recover=True,
        proposed_strategy="DOCUMENT_COMPRESSION",
        attempt_number=4 # Exceeds max 3
    )

    res = agent.execute_recovery(diagnosis, {}, "TEST_APP")
    assert res.success is False
    assert "exhausted" in res.message.lower()

def test_photo_adaptation_recovery():
    adapter = MockScholarshipPortalAdapter()
    agent = RecoveryAgent(portal_adapter=adapter, max_attempts=3)

    raw_photo = str(settings.SAMPLE_DOCS_DIR / "photo.png")
    diagnosis = FailureDiagnosis(
        failure_category="FORMAT_ERROR",
        root_cause="Dimensions mismatch",
        can_recover=True,
        proposed_strategy="IMAGE_ADAPTATION",
        attempt_number=1
    )

    res = agent.execute_recovery(diagnosis, {"file_path": raw_photo}, "TEST_APP")
    assert res.success is True
    assert "new_file_path" in res.adapted_data
    assert Path(res.adapted_data["new_file_path"]).exists()
