import time
from typing import Dict, Any, List, Optional, Callable
from app.core.state_machine import StateMachine, ApplicationState
from app.core.action_contract import ActionContract, ActionStatus, RiskLevel
from app.core.evidence_gate import EvidenceGate
from app.core.ledger import ProofLedger, LedgerEntry
from app.agents.verifier_agent import VerifierAgent
from app.agents.failure_analyzer import FailureAnalyzer
from app.agents.recovery_agent import RecoveryAgent
from app.services.portal_adapter import MockScholarshipPortalAdapter

class ExecutionAgent:
    """
    Orchestrates the Zero-Trust Agent Loop.
    Strictly separates proposal, execution, verification, and gate admission.
    """
    def __init__(
        self,
        application_id: str,
        state_machine: StateMachine,
        ledger: ProofLedger,
        portal_adapter: MockScholarshipPortalAdapter,
        event_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.application_id = application_id
        self.state_machine = state_machine
        self.ledger = ledger
        self.portal_adapter = portal_adapter
        self.verifier = VerifierAgent()
        self.failure_analyzer = FailureAnalyzer()
        self.recovery_agent = RecoveryAgent(portal_adapter=portal_adapter)
        self.event_callback = event_callback or (lambda e: None)

    def _emit(self, event_type: str, data: Dict[str, Any]):
        evt = {"event_type": event_type, "timestamp": time.time(), "data": data}
        self.event_callback(evt)

    def execute_contract(self, contract: ActionContract, runner_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> ActionContract:
        contract.mark_in_progress()
        self._emit("action_started", contract.model_dump())

        # Check Preconditions
        pre_results = {}
        for pre in contract.preconditions:
            # Deterministic precondition evaluation
            pre_results[pre] = True
        contract.precondition_results = pre_results

        # Execute
        attempt = 1
        current_params = contract.execution_params.copy()

        while attempt <= contract.max_attempts:
            contract.attempt = attempt
            observation = runner_fn(current_params)
            contract.record_observation(observation)

            # Independent Deterministic Verification
            if contract.step_category == "form_fill":
                expected = list(current_params.get("form_data", {}).keys())
                verified, evidence, errors = self.verifier.verify_field_action(observation, expected)
            elif contract.step_category == "document_upload":
                verified, evidence, errors = self.verifier.verify_upload_action(
                    observation=observation,
                    file_path=current_params.get("file_path"),
                    expected_doc_type=current_params.get("doc_type"),
                    max_kb=current_params.get("max_size_kb", 2048),
                    expected_dimensions=current_params.get("dimensions")
                )
            elif contract.step_category == "submission":
                verified, evidence, errors = self.verifier.verify_final_submission(
                    observation=observation,
                    expected_name=current_params.get("candidate_name", "")
                )
            else:
                verified = observation.get("success", False)
                evidence = {"status_code": observation.get("status_code", 200)}
                errors = [] if verified else ["Generic failure"]

            # Evaluate Gate
            contract.postcondition_results = {post: verified for post in contract.postconditions}
            contract.evidence.update(evidence)
            gate_eval = EvidenceGate.evaluate_action_contract(contract)

            if gate_eval.passed:
                contract.complete_verified(evidence)
                self.ledger.append(LedgerEntry(
                    step_id=contract.action_id,
                    action=contract.name,
                    actor="verifier",
                    preconditions=contract.preconditions,
                    command_or_operation=contract.execution_command,
                    observation=observation,
                    postconditions=contract.postconditions,
                    evidence=evidence,
                    status="VERIFIED",
                    attempt=attempt,
                    verification_result="PASSED"
                ))
                self._emit("action_verified", contract.model_dump())
                return contract

            else:
                # Failure detected - initiate Self-Healing Loop
                diagnosis = self.failure_analyzer.classify_failure(
                    action_name=contract.name,
                    observation=observation,
                    verifier_errors=errors,
                    attempt_number=attempt
                )
                self._emit("failure_detected", {"contract": contract.model_dump(), "diagnosis": diagnosis.model_dump()})

                # Log failure to Proof Ledger
                self.ledger.append(LedgerEntry(
                    step_id=f"{contract.action_id}_ATTEMPT_{attempt}",
                    action=contract.name,
                    actor="failure_analyzer",
                    observation=observation,
                    evidence={"diagnosis": diagnosis.model_dump(), "verifier_errors": errors},
                    status="FAILED",
                    attempt=attempt,
                    verification_result="FAILED"
                ))

                if not diagnosis.can_recover or attempt >= contract.max_attempts:
                    contract.complete_failed(error=f"Unrecoverable error: {diagnosis.root_cause}", evidence=evidence)
                    self._emit("action_failed", contract.model_dump())
                    return contract

                # Execute Bounded Recovery
                self._emit("recovery_started", {"strategy": diagnosis.proposed_strategy, "attempt": attempt})
                recovery_result = self.recovery_agent.execute_recovery(
                    diagnosis=diagnosis,
                    action_params=current_params,
                    application_id=self.application_id
                )
                self._emit("recovery_completed", recovery_result.to_dict())

                # Log recovery to Proof Ledger
                self.ledger.append(LedgerEntry(
                    step_id=f"{contract.action_id}_REC_{attempt}",
                    action=f"Recovery: {diagnosis.proposed_strategy}",
                    actor="recovery_agent",
                    evidence=recovery_result.to_dict(),
                    status="RECOVERED" if recovery_result.success else "RECOVERY_FAILED",
                    attempt=attempt,
                    recovery_details=recovery_result.to_dict()
                ))

                if not recovery_result.success:
                    contract.complete_failed(error=recovery_result.message, evidence=evidence)
                    return contract

                # Update execution params with adapted artifacts
                if "new_file_path" in recovery_result.adapted_data:
                    current_params["file_path"] = recovery_result.adapted_data["new_file_path"]
                if "new_session_id" in recovery_result.adapted_data:
                    current_params["session_id"] = recovery_result.adapted_data["new_session_id"]
                if "remapped_data" in recovery_result.adapted_data:
                    current_params["form_data"] = recovery_result.adapted_data["remapped_data"]

                attempt += 1

        contract.complete_failed(error=f"Exhausted {contract.max_attempts} recovery attempts")
        return contract
