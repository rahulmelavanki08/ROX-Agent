from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.core.action_contract import RiskLevel

class PlanStep(BaseModel):
    step_number: int
    title: str
    description: str
    risk_level: RiskLevel
    requires_evidence: bool = True
    estimated_duration_sec: int = 1
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED, SKIPPED

class ApplicationPlan(BaseModel):
    plan_id: str
    title: str = "Evidence-Gated Scholarship Application Execution Plan"
    steps: List[PlanStep]
    user_approved: bool = False
    modifications: List[str] = Field(default_factory=list)

class PlanningAgent:
    """
    Synthesizes and manages deterministic execution plans.
    """
    @staticmethod
    def generate_plan(schema: Dict[str, Any], has_conflicts: bool = False) -> ApplicationPlan:
        steps = [
            PlanStep(step_number=1, title="Analyze Application Schema", description="Extract field constraints, required documents, and submission criteria", risk_level=RiskLevel.LOW),
            PlanStep(step_number=2, title="Ingest & Extract User Documents", description="Extract text, tables, and provenance from uploaded documents", risk_level=RiskLevel.LOW),
            PlanStep(step_number=3, title="Cross-Document Consistency Check", description="Detect and isolate discrepancies across official identity records", risk_level=RiskLevel.MEDIUM if has_conflicts else RiskLevel.LOW),
            PlanStep(step_number=4, title="Document Adaptation Pre-flight", description="Verify file dimensions, formats, and sizes against portal constraints", risk_level=RiskLevel.LOW),
            PlanStep(step_number=5, title="Fill Personal Details Section", description="Populate candidate name, DOB, gender, category with verified evidence", risk_level=RiskLevel.LOW),
            PlanStep(step_number=6, title="Fill Academic Details Section", description="Populate institute name, registration number, and past marks", risk_level=RiskLevel.LOW),
            PlanStep(step_number=7, title="Fill Financial & Bank Details Section", description="Populate certified annual family income, bank account, and IFSC code", risk_level=RiskLevel.LOW),
            PlanStep(step_number=8, title="Upload Required Documents", description="Upload Aadhaar, marksheet, income certificate, and photo", risk_level=RiskLevel.LOW),
            PlanStep(step_number=9, title="Self-Healing Recovery on Upload Failures", description="Dynamically adapt oversized or misformatted files if portal rejects", risk_level=RiskLevel.MEDIUM),
            PlanStep(step_number=10, title="Deterministic Verification of Portal Uploads", description="Verify server receipt, checksums, and accepted file records", risk_level=RiskLevel.LOW),
            PlanStep(step_number=11, title="State Reconstruction & Draft Checkpoint", description="Query portal state, verify draft consistency, guard against timeouts", risk_level=RiskLevel.LOW),
            PlanStep(step_number=12, title="Pre-submission Audit & Consistency Gate", description="Confirm 100% field coverage and zero unresolved conflicts", risk_level=RiskLevel.MEDIUM),
            PlanStep(step_number=13, title="Present Evidence-Backed Preview", description="Display complete field audit ledger with source document citations", risk_level=RiskLevel.LOW),
            PlanStep(step_number=14, title="Irreversible Action Guard", description="Require explicit human authorization before final binding submission", risk_level=RiskLevel.HIGH),
            PlanStep(step_number=15, title="Submit & Verify Final Reference Number", description="Execute portal submission and deterministically verify reference number & receipt hash", risk_level=RiskLevel.HIGH)
        ]
        return ApplicationPlan(
            plan_id="PLAN_SCHOLARSHIP_001",
            steps=steps,
            user_approved=False
        )

    @staticmethod
    def modify_plan(plan: ApplicationPlan, modification_request: str) -> ApplicationPlan:
        plan.modifications.append(modification_request)
        # Apply modification if requested
        if "skip financial" in modification_request.lower():
            plan.steps = [s for s in plan.steps if "financial" not in s.title.lower()]
        elif "dry run" in modification_request.lower():
            plan.steps = [s for s in plan.steps if s.step_number < 14]
        # Re-number
        for i, s in enumerate(plan.steps):
            s.step_number = i + 1
        return plan
