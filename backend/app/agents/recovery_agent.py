import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings
from app.agents.failure_analyzer import FailureDiagnosis
from app.services.document_engine import DocumentEngine
from app.services.portal_adapter import MockScholarshipPortalAdapter

class RecoveryExecutionResult:
    def __init__(self, success: bool, strategy_applied: str, adapted_data: Dict[str, Any], message: str):
        self.success = success
        self.strategy_applied = strategy_applied
        self.adapted_data = adapted_data
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "strategy_applied": self.strategy_applied,
            "adapted_data": self.adapted_data,
            "message": self.message
        }

class RecoveryAgent:
    """
    Bounded Self-Healing Engine.
    Executes specific deterministic mitigation strategies based on FailureDiagnosis.
    Enforces MAX_RECOVERY_ATTEMPTS to prevent infinite loops.
    """
    def __init__(self, portal_adapter: MockScholarshipPortalAdapter, max_attempts: int = 3):
        self.portal_adapter = portal_adapter
        self.max_attempts = max_attempts

    def execute_recovery(
        self,
        diagnosis: FailureDiagnosis,
        action_params: Dict[str, Any],
        application_id: str
    ) -> RecoveryExecutionResult:
        if diagnosis.attempt_number > self.max_attempts:
            return RecoveryExecutionResult(
                success=False,
                strategy_applied=diagnosis.proposed_strategy,
                adapted_data={},
                message=f"Bounded recovery exhausted. Exceeded maximum limit of {self.max_attempts} attempts."
            )

        strategy = diagnosis.proposed_strategy
        adapted_dir = settings.STORAGE_DIR / "adapted" / application_id
        adapted_dir.mkdir(parents=True, exist_ok=True)

        # Strategy 1: Document Compression
        if strategy == "DOCUMENT_COMPRESSION":
            source_file = action_params.get("file_path")
            ext = Path(source_file).suffix.lower() if source_file else ""
            if ext in [".jpg", ".jpeg", ".png"]:
                stem = Path(source_file).stem
                out_file = str(adapted_dir / f"{stem}_adapted.jpg")
                img_res = DocumentEngine.adapt_image(
                    input_path=source_file,
                    output_path=out_file,
                    target_format="JPEG",
                    target_dimensions=(200, 230),
                    max_size_kb=95
                )
                return RecoveryExecutionResult(
                    success=img_res.get("verified", False),
                    strategy_applied="IMAGE_ADAPTATION",
                    adapted_data={"new_file_path": out_file, "adaptation_stats": img_res},
                    message=f"Image adapted: Converted to JPEG, resized to 200x230, compressed to {img_res['file_size_kb']} KB."
                )
            else:
                out_file = str(adapted_dir / f"compressed_{Path(source_file).name}")
                comp_res = DocumentEngine.compress_pdf(input_path=source_file, output_path=out_file, target_kb=1800)
                
                return RecoveryExecutionResult(
                    success=comp_res.get("verified", False),
                    strategy_applied=strategy,
                    adapted_data={"new_file_path": out_file, "compression_stats": comp_res},
                    message=f"Document successfully compressed from {comp_res['initial_size_kb']} KB to {comp_res['final_size_kb']} KB."
                )

        # Strategy 2: Image Adaptation
        elif strategy == "IMAGE_ADAPTATION":
            source_file = action_params.get("file_path")
            stem = Path(source_file).stem
            out_file = str(adapted_dir / f"{stem}_adapted.jpg")
            img_res = DocumentEngine.adapt_image(
                input_path=source_file,
                output_path=out_file,
                target_format="JPEG",
                target_dimensions=(200, 230),
                max_size_kb=95
            )

            return RecoveryExecutionResult(
                success=img_res.get("verified", False),
                strategy_applied=strategy,
                adapted_data={"new_file_path": out_file, "adaptation_stats": img_res},
                message=f"Image adapted: Converted to JPEG, resized to 200x230, compressed to {img_res['file_size_kb']} KB."
            )

        # Strategy 3: State Reconstruction & Session Resume
        elif strategy == "STATE_RECONSTRUCTION_AND_RESUME":
            old_sid = action_params.get("session_id")
            # Query server database for existing persisted state
            state = self.portal_adapter.get_application_state(old_sid)
            # Create fresh active session and restore verified checkpoint
            new_sid = self.portal_adapter.start_session()
            draft_values = state.get("draft_values", {})
            if draft_values:
                self.portal_adapter.fill_step(new_sid, "Checkpoint Restoration", draft_values)

            return RecoveryExecutionResult(
                success=True,
                strategy_applied=strategy,
                adapted_data={"new_session_id": new_sid, "restored_fields": list(draft_values.keys())},
                message=f"Application state reconstructed. Restored {len(draft_values)} fields into active session {new_sid}."
            )

        # Strategy 4: Reconcile Server State for Timeout / Unknown State
        elif strategy == "RECONCILE_SERVER_STATE":
            sid = action_params.get("session_id")
            state = self.portal_adapter.get_application_state(sid)
            submitted_fields = action_params.get("data", {})
            persisted = state.get("persisted_fields", [])
            
            all_persisted = all(f in persisted for f in submitted_fields.keys())
            return RecoveryExecutionResult(
                success=all_persisted,
                strategy_applied=strategy,
                adapted_data={"persisted_on_server": all_persisted, "server_fields": persisted},
                message="Server state reconciled: Fields were successfully received despite gateway timeout." if all_persisted else "Server state reconciled: Data not found, re-try required."
            )

        # Strategy 5: Remap Field Schema
        elif strategy == "REMAP_FIELD_SCHEMA":
            data = action_params.get("data", {}).copy()
            if "annual_family_income" in data:
                val = data.pop("annual_family_income")
                data["annual_income_revised"] = val

            return RecoveryExecutionResult(
                success=True,
                strategy_applied=strategy,
                adapted_data={"remapped_data": data},
                message="Field schema remapped to match updated portal requirement."
            )

        return RecoveryExecutionResult(
            success=False,
            strategy_applied=strategy,
            adapted_data={},
            message=f"No automated recovery handler implemented for strategy '{strategy}'."
        )
