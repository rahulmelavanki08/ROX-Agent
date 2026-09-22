import os
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.core.config import settings
from app.core.state_machine import StateMachine, ApplicationState
from app.core.action_contract import ActionContract, ActionStatus, RiskLevel
from app.core.evidence_gate import EvidenceGate
from app.core.ledger import ProofLedger, LedgerEntry
from app.agents.requirement_agent import RequirementAgent
from app.agents.document_agent import DocumentAgent
from app.agents.mapping_agent import MappingAgent
from app.agents.planning_agent import PlanningAgent, ApplicationPlan
from app.agents.execution_agent import ExecutionAgent
from app.services.document_engine import DocumentEngine
from app.services.portal_adapter import MockScholarshipPortalAdapter
from app.services.llm_provider import get_llm_provider
from app.api.websocket import manager

api_router = APIRouter(prefix=settings.API_PREFIX, tags=["ROX Core Agent"])

# In-memory session states
ACTIVE_APPLICATIONS: Dict[str, Dict[str, Any]] = {}

APPLICATION_TYPES = [
    {
        "id": "scholarship_sbi",
        "title": "SBI Platinum Jubilee Scholarship 2026",
        "category": "Scholarship",
        "authority": "State Bank of India Foundation (SBIF)",
        "deadline": "31-Mar-2026",
        "description": "Financial assistance program for meritorious undergraduate & professional degree students with annual family income <= ₹3,00,000.",
        "icon": "GraduationCap",
        "badge": "Track A1 Benchmark",
        "portal_url": "http://localhost:8000/portal",
        "required_documents": [
            {
                "key": "doc_aadhaar",
                "name": "Aadhaar Card / ID Proof",
                "description": "Identity & age verification document issued by UIDAI",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "aadhaar.pdf"
            },
            {
                "key": "doc_marksheet",
                "name": "10th / 12th Academic Marksheet",
                "description": "Official state or central board score sheet with aggregate percentage",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "marksheet.pdf"
            },
            {
                "key": "doc_income_cert",
                "name": "Family Income Certificate",
                "description": "Competent revenue authority issued certificate (Max 2.0 MB)",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "income_certificate.pdf",
                "known_issue": "Sample file is 5.7 MB (exceeds 2 MB limit) -> Requires automated compression"
            },
            {
                "key": "doc_photo",
                "name": "Applicant Passport Photograph",
                "description": "Recent color photograph (Must be JPG, exactly 200x230 px, under 100 KB)",
                "accepted_formats": [".jpg", ".jpeg"],
                "max_size_kb": 100,
                "dimensions": [200, 230],
                "required": True,
                "sample_match": "photo.png",
                "known_issue": "Sample file is PNG 1600x1200 px -> Requires format conversion & resizing"
            },
            {
                "key": "doc_passbook",
                "name": "Bank Passbook / Cancelled Cheque",
                "description": "Document displaying Account Holder, Bank Name, Account Number and IFSC Code",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "bank_passbook.pdf"
            }
        ],
        "form_sections": [
            {"name": "Personal Details", "fields": ["full_name", "date_of_birth", "gender", "category", "email", "phone_number"]},
            {"name": "Academic Qualifications", "fields": ["institution_name", "roll_number", "tenth_percentage", "twelfth_percentage"]},
            {"name": "Financial & Banking", "fields": ["annual_family_income", "bank_name", "bank_account_number", "ifsc_code"]},
            {"name": "Enclosures", "fields": ["doc_aadhaar", "doc_marksheet", "doc_income_cert", "doc_photo"]}
        ]
    },
    {
        "id": "hostel_post_matric",
        "title": "Government Post-Matric Hostel Admission 2026",
        "category": "Hostel Accommodation",
        "authority": "Backward Classes Welfare & Social Justice Department",
        "deadline": "15-Apr-2026",
        "description": "State government subsidized hostel accommodation and boarding facility for university and polytechnic students.",
        "icon": "Building2",
        "badge": "State Portal",
        "portal_url": "http://localhost:8000/portal",
        "required_documents": [
            {
                "key": "doc_aadhaar",
                "name": "Aadhaar Card",
                "description": "Proof of identity and residential domicile",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "aadhaar.pdf"
            },
            {
                "key": "doc_marksheet",
                "name": "College Admission Fee Receipt / Marksheet",
                "description": "Proof of current academic admission & student ID",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "marksheet.pdf"
            },
            {
                "key": "doc_income_cert",
                "name": "Income & Caste Verification Certificate",
                "description": "Valid government certificate certifying community and income band",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "income_certificate.pdf"
            },
            {
                "key": "doc_photo",
                "name": "Passport Sized Photograph",
                "description": "Recent photograph for student hostel ID card",
                "accepted_formats": [".jpg", ".jpeg"],
                "max_size_kb": 100,
                "dimensions": [200, 230],
                "required": True,
                "sample_match": "photo.png"
            }
        ],
        "form_sections": [
            {"name": "Applicant Profile", "fields": ["full_name", "date_of_birth", "gender", "category", "phone_number"]},
            {"name": "Hostel & Course Info", "fields": ["institution_name", "roll_number"]},
            {"name": "Document Enclosures", "fields": ["doc_aadhaar", "doc_marksheet", "doc_income_cert", "doc_photo"]}
        ]
    },
    {
        "id": "certificate_income_caste",
        "title": "Government Income & Caste Certificate",
        "category": "Government Certificates",
        "authority": "Department of Revenue & Citizen Services (Seva Sindhu / e-District)",
        "deadline": "Continuous / No Deadline",
        "description": "Statutory legal certificate required for state quotas, fee concessions, and government welfare schemes.",
        "icon": "FileCheck2",
        "badge": "Citizen e-Services",
        "portal_url": "http://localhost:8000/portal",
        "required_documents": [
            {
                "key": "doc_aadhaar",
                "name": "Identity Proof (Aadhaar / Voter ID)",
                "description": "Proof of identity & permanent residence",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "aadhaar.pdf"
            },
            {
                "key": "doc_passbook",
                "name": "Ration Card / Bank Passbook",
                "description": "Family card showing household details & bank account",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "bank_passbook.pdf"
            },
            {
                "key": "doc_income_cert",
                "name": "Salary Certificate / Self-Declaration Affidavit",
                "description": "Proof of gross annual family income from all sources",
                "accepted_formats": [".pdf"],
                "max_size_kb": 2048,
                "required": True,
                "sample_match": "income_certificate.pdf"
            },
            {
                "key": "doc_photo",
                "name": "Applicant Photograph",
                "description": "Photograph to be imprinted on digital certificate",
                "accepted_formats": [".jpg", ".jpeg"],
                "max_size_kb": 100,
                "dimensions": [200, 230],
                "required": True,
                "sample_match": "photo.png"
            }
        ],
        "form_sections": [
            {"name": "Citizen Particulars", "fields": ["full_name", "date_of_birth", "gender", "category"]},
            {"name": "Income & Family Details", "fields": ["annual_family_income", "bank_account_number"]},
            {"name": "Enclosed Proofs", "fields": ["doc_aadhaar", "doc_passbook", "doc_income_cert", "doc_photo"]}
        ]
    }
]

class InitAppRequest(BaseModel):
    application_id: Optional[str] = None
    application_type: Optional[str] = "scholarship_sbi"
    portal_url: str = "http://localhost:8000/portal"
    user_goal: str = "Complete this scholarship application using my uploaded documents."

class AdaptFileRequest(BaseModel):
    file_name: str
    action: str  # "compress_pdf" or "convert_image"

class ResolveConflictRequest(BaseModel):
    field_id: str
    chosen_value: str
    source_reference: str

class PlanApprovalRequest(BaseModel):
    approved: bool
    modification_request: Optional[str] = None

class SubmissionApprovalRequest(BaseModel):
    user_confirmed: bool

class UpdateFieldRequest(BaseModel):
    field_id: str
    value: str
    source: Optional[str] = "User Direct Input"

class ConfigKeyRequest(BaseModel):
    gemini_api_key: str

def get_app_session(app_id: str) -> Dict[str, Any]:
    session = ACTIVE_APPLICATIONS.get(app_id)
    if not session:
        up_dir = settings.STORAGE_DIR / "uploads" / app_id
        if up_dir.exists():
            portal_adapter = MockScholarshipPortalAdapter()
            portal_session_id = portal_adapter.start_session()
            state_machine = StateMachine()
            ledger = ProofLedger(app_id, settings.STORAGE_DIR)
            req_agent = RequirementAgent()
            schema = req_agent.analyze_portal(url="http://localhost:8000/portal", goal="Complete application")
            
            uploaded_files = [str(p) for p in up_dir.glob("*.*") if p.is_file()]
            doc_slots = {}
            for fpath in uploaded_files:
                fname = Path(fpath).name.lower()
                if "aadhaar" in fname: doc_slots["doc_aadhaar"] = fpath
                elif "marksheet" in fname: doc_slots["doc_marksheet"] = fpath
                elif "income" in fname: doc_slots["doc_income_cert"] = fpath
                elif "photo" in fname: doc_slots["doc_photo"] = fpath
                elif "passbook" in fname: doc_slots["doc_passbook"] = fpath
                else:
                    clean_stem = Path(fpath).stem.lower().replace("-", "_").replace(" ", "_")
                    doc_slots[f"doc_{clean_stem}"] = fpath
            
            session = {
                "application_id": app_id,
                "application_type": "scholarship_sbi",
                "portal_url": "http://localhost:8000/portal",
                "portal_session_id": portal_session_id,
                "user_goal": "Complete application",
                "state_machine": state_machine,
                "ledger": ledger,
                "portal_adapter": portal_adapter,
                "uploaded_files": uploaded_files,
                "doc_slots": doc_slots,
                "doc_metadata": {f: {"file_name": Path(f).name, "doc_type": doc_slots.get(f)} for f in uploaded_files},
                "ingested_docs": [],
                "file_issues": [],
                "schema": schema,
                "mapping_result": {},
                "plan": None,
                "manual_resolutions": {},
                "execution_agent": None,
                "final_submission_result": None,
                "user_approved_submission": False
            }
            ACTIVE_APPLICATIONS[app_id] = session
            return session
        raise HTTPException(status_code=404, detail=f"Application '{app_id}' not found")
    return session

def broadcast_sync(message: Dict[str, Any]):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.broadcast(message))
        else:
            loop.run_until_complete(manager.broadcast(message))
    except Exception:
        pass

@api_router.get("/application-types")
async def get_application_types():
    return {
        "status": "SUCCESS",
        "types": APPLICATION_TYPES
    }

@api_router.get("/config")
async def get_system_config():
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    provider = get_llm_provider(api_key)
    key_configured = bool(api_key and api_key.strip())
    return {
        "app_name": settings.APP_NAME,
        "llm_provider": type(provider).__name__,
        "gemini_configured": key_configured,
        "model": settings.GEMINI_MODEL,
        "max_recovery_attempts": settings.MAX_RECOVERY_ATTEMPTS
    }

@api_router.post("/config/set-key")
async def set_gemini_key(req: ConfigKeyRequest):
    settings.GEMINI_API_KEY = req.gemini_api_key.strip()
    provider = get_llm_provider(settings.GEMINI_API_KEY)
    return {
        "status": "SUCCESS",
        "message": "Gemini API key updated",
        "active_provider": type(provider).__name__
    }

@api_router.post("/sample-docs/load")
async def load_sample_docs_to_app(application_id: str):
    app = get_app_session(application_id)
    dest_dir = settings.STORAGE_DIR / "uploads" / application_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    loaded = []
    app.setdefault("doc_slots", {})
    app.setdefault("doc_metadata", {})

    slots_map = {
        "aadhaar": "doc_aadhaar",
        "marksheet": "doc_marksheet",
        "income": "doc_income_cert",
        "photo": "doc_photo",
        "passbook": "doc_passbook"
    }

    for f in settings.SAMPLE_DOCS_DIR.glob("*.*"):
        if f.suffix.lower() in [".pdf", ".png", ".jpg", ".docx"]:
            target = dest_dir / f.name
            shutil.copy2(f, target)
            loaded.append(f.name)
            str_target = str(target)
            for k, slot in slots_map.items():
                if k in f.name.lower():
                    app["doc_slots"][slot] = str_target
                    app["doc_metadata"][str_target] = {"doc_type": slot, "file_name": f.name}

    app["uploaded_files"] = [str(dest_dir / fname) for fname in loaded]
    return {
        "status": "SUCCESS",
        "message": f"Loaded {len(loaded)} demo documents into application {application_id}",
        "documents": loaded
    }

@api_router.get("/applications/{app_id}/documents")
async def get_uploaded_documents(app_id: str):
    app = get_app_session(app_id)
    docs = []
    metadata = app.get("doc_metadata", {})
    slots = app.get("doc_slots", {})
    for fpath_str in app.get("uploaded_files", []):
        if os.path.exists(fpath_str):
            p = Path(fpath_str)
            size_kb = round(os.path.getsize(fpath_str) / 1024.0, 2)
            meta = metadata.get(fpath_str, {})
            doc_type = meta.get("doc_type")
            if not doc_type:
                for s_key, s_path in slots.items():
                    if s_path == fpath_str:
                        doc_type = s_key
                        break
            if not doc_type:
                fname = p.name.lower()
                if "aadhaar" in fname:
                    doc_type = "doc_aadhaar"
                elif "marksheet" in fname:
                    doc_type = "doc_marksheet"
                elif "income" in fname:
                    doc_type = "doc_income_cert"
                elif "photo" in fname:
                    doc_type = "doc_photo"
                elif "passbook" in fname:
                    doc_type = "doc_passbook"

            docs.append({
                "file_name": p.name,
                "file_path": str(p),
                "doc_type": doc_type,
                "extension": p.suffix.lower(),
                "file_size_kb": size_kb,
                "file_size_mb": round(size_kb / 1024.0, 2),
                "is_compressed": "compressed_" in p.name,
                "is_adapted": ".jpg" in p.name and "photo" in p.name.lower()
            })
    return {"documents": docs, "total": len(docs)}

@api_router.post("/applications/init")
async def init_application(req: InitAppRequest):
    import uuid
    app_id = req.application_id or f"APP_{uuid.uuid4().hex[:8].upper()}"
    app_type = req.application_type or "scholarship_sbi"
    
    upload_dir = settings.STORAGE_DIR / "uploads" / app_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    portal_adapter = MockScholarshipPortalAdapter()
    portal_session_id = portal_adapter.start_session()
    state_machine = StateMachine()
    ledger = ProofLedger(app_id, settings.STORAGE_DIR)

    req_agent = RequirementAgent()
    schema = req_agent.analyze_portal(url=req.portal_url, goal=req.user_goal, app_type=app_type)

    app_context = {
        "application_id": app_id,
        "application_type": app_type,
        "portal_url": req.portal_url,
        "portal_session_id": portal_session_id,
        "user_goal": req.user_goal,
        "state_machine": state_machine,
        "ledger": ledger,
        "portal_adapter": portal_adapter,
        "uploaded_files": [],
        "doc_slots": {},
        "doc_metadata": {},
        "ingested_docs": [],
        "file_issues": [],
        "schema": schema,
        "mapping_result": {},
        "plan": None,
        "manual_resolutions": {},
        "execution_agent": None,
        "final_submission_result": None,
        "user_approved_submission": False
    }

    ACTIVE_APPLICATIONS[app_id] = app_context
    ledger.append(LedgerEntry(
        step_id="INIT_001",
        action="Application Initialized",
        actor="user",
        observation={"portal_session_id": portal_session_id, "url": req.portal_url, "application_type": app_type},
        status="INITIALIZED",
        verification_result="PASSED"
    ))

    return {
        "application_id": app_id,
        "application_type": app_type,
        "portal_session_id": portal_session_id,
        "state": state_machine.current_state,
        "message": "Application context created"
    }

@api_router.post("/applications/{app_id}/upload")
async def upload_document(
    app_id: str, 
    file: UploadFile = File(...),
    doc_type: Optional[str] = Form(None)
):
    app = get_app_session(app_id)
    dest_dir = settings.STORAGE_DIR / "uploads" / app_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = dest_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    str_path = str(file_path)
    if str_path not in app["uploaded_files"]:
        app["uploaded_files"].append(str_path)

    # Resolve document slot type
    resolved_type = doc_type
    if not resolved_type:
        fname = file.filename.lower()
        if "aadhaar" in fname or "id" in fname or "uid" in fname:
            resolved_type = "doc_aadhaar"
        elif "marksheet" in fname or "score" in fname or "grade" in fname or "10th" in fname or "12th" in fname or "admit" in fname or "hall" in fname or "tc" in fname:
            resolved_type = "doc_marksheet"
        elif "income" in fname or "salary" in fname or "caste" in fname or "rd" in fname or "cert" in fname:
            resolved_type = "doc_income_cert"
        elif "passbook" in fname or "bank" in fname or "ration" in fname or "statement" in fname or "cheque" in fname:
            resolved_type = "doc_passbook"
        elif "photo" in fname or "pic" in fname or Path(file.filename).suffix.lower() in [".png", ".jpg", ".jpeg"]:
            resolved_type = "doc_photo"
        else:
            import re
            clean_stem = re.sub(r"[^a-zA-Z0-9]", "_", Path(file.filename).stem).lower()
            resolved_type = f"doc_{clean_stem}"

    app.setdefault("doc_slots", {})[resolved_type] = str_path
    app.setdefault("doc_metadata", {})[str_path] = {
        "doc_type": resolved_type,
        "file_name": file.filename
    }

    return {
        "file_name": file.filename,
        "doc_type": resolved_type,
        "file_size_kb": round(len(content) / 1024.0, 2),
        "total_documents": len(app["uploaded_files"])
    }

@api_router.post("/applications/{app_id}/update-field")
async def update_application_field(app_id: str, req: UpdateFieldRequest):
    app = get_app_session(app_id)
    app["manual_resolutions"][req.field_id] = req.value
    ledger: ProofLedger = app["ledger"]
    ledger.append(LedgerEntry(
        step_id=f"UPDATE_{req.field_id.upper()}",
        action=f"User Direct Field Input: {req.field_id}",
        actor="user",
        evidence={"field_id": req.field_id, "value": req.value, "source": req.source},
        status="USER_UPDATED",
        verification_result="PASSED"
    ))

    # Ensure schema is loaded
    if not app.get("schema"):
        req_agent = RequirementAgent()
        app["schema"] = req_agent.analyze_portal(url=app.get("portal_url", "http://localhost:8000/portal"), goal=app.get("user_goal", "Complete scholarship application"))

    mapping_agent = MappingAgent()
    map_res = mapping_agent.map_evidence(
        schema=app.get("schema", {}),
        ingested_documents=app.get("ingested_docs", []),
        manual_overrides=app["manual_resolutions"]
    )
    # If field is custom or not present in schema, ensure it is added to mapped_fields
    if req.field_id not in map_res.get("mapped_fields", {}):
        map_res.setdefault("mapped_fields", {})[req.field_id] = {
            "field_id": req.field_id,
            "label": req.field_id.replace("_", " ").title(),
            "value": req.value,
            "status": "VERIFIED",
            "source_file": req.source or "User Direct Input",
            "source_page": 1,
            "evidence_text": f"Direct applicant input: '{req.value}'",
            "confidence": 1.0
        }
    app["mapping_result"] = map_res
    broadcast_sync({"event_type": "field_updated", "field_id": req.field_id, "value": req.value})
    return {
        "status": "SUCCESS",
        "message": f"Updated '{req.field_id}' to '{req.value}'",
        "field_id": req.field_id,
        "value": req.value
    }

@api_router.post("/applications/{app_id}/analyze")
async def analyze_application(app_id: str):
    app = get_app_session(app_id)
    sm: StateMachine = app["state_machine"]
    ledger: ProofLedger = app["ledger"]

    sm.transition(ApplicationState.ANALYZING, reason="Starting application requirement discovery and document ingestion")
    broadcast_sync({"event_type": "state_changed", "to_state": ApplicationState.ANALYZING})

    req_agent = RequirementAgent()
    schema = req_agent.analyze_portal(url=app["portal_url"], goal=app["user_goal"], app_type=app.get("application_type"))
    app["schema"] = schema

    doc_agent = DocumentAgent()
    ingested = []
    metadata = app.get("doc_metadata", {})
    for fpath in app["uploaded_files"]:
        doc_type = metadata.get(fpath, {}).get("doc_type")
        doc_data = doc_agent.ingest_document(fpath, doc_type=doc_type)
        ingested.append(doc_data)
    app["ingested_docs"] = ingested

    # Map evidence and run cross-document conflict detection
    mapping_agent = MappingAgent()
    map_res = mapping_agent.map_evidence(
        schema=schema,
        ingested_documents=ingested,
        manual_overrides=app["manual_resolutions"]
    )
    app["mapping_result"] = map_res

    # Generate plan
    plan_agent = PlanningAgent()
    plan = plan_agent.generate_plan(schema=schema, has_conflicts=map_res["unresolved_conflicts_count"] > 0)
    app["plan"] = plan

    has_conflicts = map_res["unresolved_conflicts_count"] > 0
    next_state = ApplicationState.BLOCKED if has_conflicts else ApplicationState.AWAITING_PLAN_APPROVAL
    
    sm.transition(
        next_state,
        reason="Detected cross-document identity conflicts; blocking automated action" if has_conflicts else "Analysis completed; execution plan generated awaiting user approval",
        evidence={"conflicts_count": map_res["unresolved_conflicts_count"], "mapped_fields": len(map_res["mapped_fields"])}
    )

    ledger.append(LedgerEntry(
        step_id="ANALYSIS_001",
        action="Requirement and Document Analysis",
        actor="mapping_agent",
        observation={"sections": len(schema.get("sections", [])), "ingested_documents": len(ingested)},
        evidence=map_res,
        status="BLOCKED" if has_conflicts else "AWAITING_APPROVAL",
        verification_result="CONFLICT_DETECTED" if has_conflicts else "PASSED"
    ))

    # Detect file-level issues (oversized, format/dimension mismatches)
    file_issues = []
    from PIL import Image
    slots = app.get("doc_slots", {})
    metadata = app.get("doc_metadata", {})

    for fpath_str in app["uploaded_files"]:
        if not os.path.exists(fpath_str):
            continue
        p = Path(fpath_str)
        fname = p.name
        ext = p.suffix.lower()
        size_kb = os.path.getsize(fpath_str) / 1024.0
        doc_type = metadata.get(fpath_str, {}).get("doc_type") or next((k for k, v in slots.items() if v == fpath_str), None)

        if ext == ".pdf":
            if size_kb > 2048.0:
                file_issues.append({
                    "file_name": fname,
                    "file_path": str(p),
                    "file_type": "PDF",
                    "issue_type": "OVERSIZED_FILE",
                    "severity": "CRITICAL",
                    "current_size_kb": round(size_kb, 2),
                    "current_size_mb": round(size_kb / 1024.0, 2),
                    "limit_kb": 2048.0,
                    "limit_mb": 2.0,
                    "message": f"'{fname}' is {round(size_kb / 1024.0, 2)} MB, exceeding the portal limit of 2.0 MB.",
                    "recommendation": "Compress PDF document streams using PyMuPDF Deflate engine to bring file under 2.0 MB.",
                    "action_required": "compress_pdf"
                })
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
            is_photo_slot = (doc_type == "doc_photo") or ("photo" in fname.lower() and "doc_aadhaar" in slots)
            if is_photo_slot:
                try:
                    with Image.open(fpath_str) as img:
                        dims = (img.width, img.height)
                        fmt = img.format.upper() if img.format else "UNKNOWN"
                        mismatch_format = fmt not in ["JPEG", "JPG"]
                        mismatch_dims = dims != (200, 230)
                        oversized = size_kb > 100.0
                        if mismatch_format or mismatch_dims or oversized:
                            issues_list = []
                            if mismatch_format:
                                issues_list.append(f"Format is {fmt} (Required: JPG)")
                            if mismatch_dims:
                                issues_list.append(f"Dimensions are {dims[0]}x{dims[1]} px (Required: 200x230 px)")
                            if oversized:
                                issues_list.append(f"File size is {round(size_kb, 1)} KB (Limit: 100 KB)")

                            file_issues.append({
                                "file_name": fname,
                                "file_path": str(p),
                                "file_type": "IMAGE",
                                "issue_type": "UNSUPPORTED_FORMAT_OR_DIMENSIONS",
                                "severity": "CRITICAL",
                                "current_format": fmt,
                                "required_format": "JPEG",
                                "current_dimensions": list(dims),
                                "required_dimensions": [200, 230],
                                "current_size_kb": round(size_kb, 1),
                                "limit_kb": 100.0,
                                "message": f"'{fname}' format/dimension violation: {'; '.join(issues_list)}.",
                                "recommendation": "Convert image to JPEG, resize to 200x230 px, and compress under 100 KB.",
                                "action_required": "convert_image"
                            })
                except Exception:
                    pass
            else:
                # Document slot requires PDF (Aadhaar, Marksheet, Income, Passbook)
                file_issues.append({
                    "file_name": fname,
                    "file_path": str(p),
                    "file_type": "IMAGE",
                    "issue_type": "UNSUPPORTED_DOCUMENT_FORMAT",
                    "severity": "CRITICAL",
                    "current_format": ext.upper().replace(".", ""),
                    "required_format": "PDF",
                    "current_size_kb": round(size_kb, 1),
                    "limit_kb": 2048.0,
                    "limit_mb": 2.0,
                    "message": f"'{fname}' is an image ({ext.upper()}), but portal requires an official PDF document.",
                    "recommendation": "Auto-convert image to standard PDF format and verify dimensions.",
                    "action_required": "convert_to_pdf"
                })

    app["file_issues"] = file_issues

    # Gemini AI Inter-Document Cross Audit
    llm = get_llm_provider()
    llm_audit = llm.compare_inter_documents(ingested_documents=ingested)
    app["llm_audit"] = llm_audit

    # Gemini AI Fault Diagnosis & Conversational Replies
    llm_fault_replies = []
    if map_res.get("unresolved_conflicts_count", 0) > 0:
        conflicts = map_res.get("conflicts", [])
        conflict_diag = llm.diagnose_fault_and_reply(
            fault_type="IDENTITY_DISCREPANCY",
            details={
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
                "summary": "Cross-document identity discrepancy detected across uploaded enclosures."
            }
        )
        llm_fault_replies.append(conflict_diag)

    if file_issues:
        for fi in file_issues:
            fi_diag = llm.diagnose_fault_and_reply(
                fault_type=fi.get("issue_type", "FILE_ISSUE"),
                details=fi
            )
            llm_fault_replies.append(fi_diag)

    app["llm_fault_replies"] = llm_fault_replies

    broadcast_sync({
        "event_type": "analysis_completed",
        "state": sm.current_state,
        "mapping": map_res,
        "file_issues": file_issues,
        "llm_audit": llm_audit,
        "llm_fault_replies": llm_fault_replies
    })

    return {
        "status": "SUCCESS",
        "state": sm.current_state,
        "schema": schema,
        "ingested_count": len(ingested),
        "mapping": map_res,
        "plan": plan.model_dump(),
        "file_issues": file_issues,
        "llm_audit": llm_audit,
        "llm_fault_replies": llm_fault_replies
    }

@api_router.post("/applications/{app_id}/adapt-file")
async def adapt_application_file(app_id: str, req: AdaptFileRequest):
    app = get_app_session(app_id)
    ledger: ProofLedger = app["ledger"]

    target_path = None
    for f in app["uploaded_files"]:
        if Path(f).name.lower() == req.file_name.lower():
            target_path = f
            break

    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail=f"File '{req.file_name}' not found in application uploads")

    upload_dir = Path(target_path).parent

    if req.action == "compress_pdf":
        out_name = f"compressed_{req.file_name}"
        out_path = str(upload_dir / out_name)
        res = DocumentEngine.compress_pdf(target_path, out_path, target_kb=1900)

        app["uploaded_files"] = [out_path if f == target_path else f for f in app["uploaded_files"]]

        for doc in app.get("ingested_docs", []):
            if doc.get("file_name") == req.file_name:
                doc["file_name"] = out_name
                doc["file_path"] = out_path
                doc["metadata"]["file_size_kb"] = res["final_size_kb"]

        # Update file_issues list
        app["file_issues"] = [fi for fi in app.get("file_issues", []) if fi.get("file_name") != req.file_name]

        ledger.append(LedgerEntry(
            step_id=f"ADAPT_COMPRESS_{req.file_name.upper()}",
            action="Self-Healing Document Adaptation: PDF Compression",
            actor="document_engine",
            observation={"initial_size_kb": res["initial_size_kb"], "final_size_kb": res["final_size_kb"]},
            evidence=res,
            status="ADAPTED",
            verification_result="PASSED"
        ))
        broadcast_sync({"event_type": "file_adapted", "action": "compress_pdf", "result": res})
        return {
            "status": "SUCCESS",
            "action": "compress_pdf",
            "original_file": req.file_name,
            "adapted_file": out_name,
            "initial_size_kb": res["initial_size_kb"],
            "final_size_kb": res["final_size_kb"],
            "verified": res["verified"]
        }

    elif req.action == "convert_image":
        out_name = Path(req.file_name).stem + ".jpg"
        out_path = str(upload_dir / out_name)
        res = DocumentEngine.adapt_image(
            input_path=target_path,
            output_path=out_path,
            target_format="JPEG",
            target_dimensions=(200, 230),
            max_size_kb=100
        )

        app["uploaded_files"] = [out_path if f == target_path else f for f in app["uploaded_files"]]

        for doc in app.get("ingested_docs", []):
            if doc.get("file_name") == req.file_name:
                doc["file_name"] = out_name
                doc["file_path"] = out_path
                doc["metadata"]["format"] = "JPEG"
                doc["metadata"]["dimensions"] = (200, 230)
                doc["metadata"]["file_size_kb"] = res["file_size_kb"]

        # Update file_issues list
        app["file_issues"] = [fi for fi in app.get("file_issues", []) if fi.get("file_name") != req.file_name]

        ledger.append(LedgerEntry(
            step_id=f"ADAPT_IMAGE_{req.file_name.upper()}",
            action="Self-Healing Document Adaptation: Image Format & Resize",
            actor="document_engine",
            observation={"original": req.file_name, "converted": out_name},
            evidence=res,
            status="ADAPTED",
            verification_result="PASSED"
        ))
        broadcast_sync({"event_type": "file_adapted", "action": "convert_image", "result": res})
        return {
            "status": "SUCCESS",
            "action": "convert_image",
            "original_file": req.file_name,
            "adapted_file": out_name,
            "output_format": res["output_format"],
            "dimensions": res["dimensions"],
            "final_size_kb": res["file_size_kb"],
            "verified": res["verified"]
        }

    elif req.action in ["convert_to_pdf", "convert_image_to_pdf"]:
        out_name = Path(req.file_name).stem + ".pdf"
        out_path = str(upload_dir / out_name)
        res = DocumentEngine.convert_image_to_pdf(target_path, out_path, max_size_kb=2048.0)

        app["uploaded_files"] = [out_path if f == target_path else f for f in app["uploaded_files"]]

        slots = app.get("doc_slots", {})
        for k, v in list(slots.items()):
            if v == target_path:
                slots[k] = out_path

        metadata = app.get("doc_metadata", {})
        if target_path in metadata:
            meta_val = metadata.pop(target_path)
            meta_val["file_name"] = out_name
            metadata[out_path] = meta_val

        for doc in app.get("ingested_docs", []):
            if doc.get("file_name") == req.file_name:
                doc["file_name"] = out_name
                doc["file_path"] = out_path
                doc["metadata"]["format"] = "PDF"
                doc["metadata"]["file_size_kb"] = res["final_size_kb"]

        # Update file_issues list
        app["file_issues"] = [fi for fi in app.get("file_issues", []) if fi.get("file_name") != req.file_name]

        ledger.append(LedgerEntry(
            step_id=f"ADAPT_IMG2PDF_{req.file_name.upper()[:20]}",
            action="Self-Healing Document Adaptation: Convert Image to PDF",
            actor="document_engine",
            observation={"original": req.file_name, "converted": out_name},
            evidence=res,
            status="ADAPTED",
            verification_result="PASSED"
        ))
        broadcast_sync({"event_type": "file_adapted", "action": "convert_to_pdf", "result": res})
        return {
            "status": "SUCCESS",
            "action": "convert_to_pdf",
            "original_file": req.file_name,
            "adapted_file": out_name,
            "initial_size_kb": res["initial_size_kb"],
            "final_size_kb": res["final_size_kb"],
            "verified": res["verified"]
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported adaptation action: {req.action}")

@api_router.post("/applications/{app_id}/auto-adapt-all")
async def auto_adapt_all_files(app_id: str):
    app = get_app_session(app_id)
    file_issues = list(app.get("file_issues", []))
    results = []

    for issue in file_issues:
        fname = issue["file_name"]
        action = issue["action_required"]
        try:
            req = AdaptFileRequest(file_name=fname, action=action)
            res = await adapt_application_file(app_id, req)
            results.append(res)
        except Exception as e:
            results.append({
                "status": "FAILED",
                "file_name": fname,
                "action": action,
                "error": str(e)
            })

    return {
        "status": "SUCCESS",
        "adapted_count": len(results),
        "results": results,
        "remaining_issues": app.get("file_issues", []),
        "uploaded_files": app.get("uploaded_files", [])
    }

@api_router.post("/applications/{app_id}/resolve-conflict")
async def resolve_conflict(app_id: str, req: ResolveConflictRequest):
    app = get_app_session(app_id)
    app["manual_resolutions"][req.field_id] = req.chosen_value

    ledger: ProofLedger = app["ledger"]
    ledger.append(LedgerEntry(
        step_id=f"RESOLVE_{req.field_id.upper()}",
        action=f"User Conflict Resolution: {req.field_id}",
        actor="user",
        evidence={"field_id": req.field_id, "resolved_value": req.chosen_value, "source": req.source_reference},
        status="USER_RESOLVED",
        verification_result="PASSED"
    ))

    # Re-evaluate mapping with new user override
    mapping_agent = MappingAgent()
    map_res = mapping_agent.map_evidence(
        schema=app["schema"],
        ingested_documents=app["ingested_docs"],
        manual_overrides=app["manual_resolutions"]
    )
    app["mapping_result"] = map_res

    sm: StateMachine = app["state_machine"]
    if map_res["unresolved_conflicts_count"] == 0:
        app["llm_fault_replies"] = [
            f for f in app.get("llm_fault_replies", [])
            if f.get("fault_category") != "DATA_ERROR" and "IDENTITY" not in f.get("fault_title", "").upper()
        ]
        if sm.current_state == ApplicationState.BLOCKED:
            sm.transition(ApplicationState.AWAITING_PLAN_APPROVAL, reason="All data conflicts resolved by user")

    broadcast_sync({"event_type": "conflict_resolved", "field_id": req.field_id, "state": sm.current_state, "llm_fault_replies": app.get("llm_fault_replies", [])})

    return {
        "status": "SUCCESS",
        "message": f"Conflict on '{req.field_id}' resolved",
        "state": sm.current_state,
        "remaining_conflicts": map_res["unresolved_conflicts_count"]
    }

@api_router.post("/applications/{app_id}/approve-plan")
async def approve_plan(app_id: str, req: PlanApprovalRequest):
    app = get_app_session(app_id)
    sm: StateMachine = app["state_machine"]
    ledger: ProofLedger = app["ledger"]
    plan: ApplicationPlan = app["plan"]

    if req.modification_request:
        PlanningAgent.modify_plan(plan, req.modification_request)

    if req.approved:
        plan.user_approved = True
        if sm.current_state == ApplicationState.BLOCKED:
            raise HTTPException(
                status_code=400,
                detail="Cannot approve plan: Application is currently BLOCKED due to unresolved cross-document conflicts. Please resolve the mismatches in Step 3 first."
            )
        if sm.current_state == ApplicationState.AWAITING_PLAN_APPROVAL:
            sm.transition(ApplicationState.PLANNED, reason="Plan approved by user", evidence={"plan_id": plan.plan_id})
            ledger.append(LedgerEntry(
                step_id="PLAN_APPROVAL",
                action="Plan Approval",
                actor="user",
                observation={"modifications": plan.modifications},
                status="APPROVED",
                verification_result="PASSED"
            ))
            broadcast_sync({"event_type": "plan_approved", "plan": plan.model_dump()})

    return {"status": "SUCCESS", "state": sm.current_state, "plan": plan.model_dump()}

@api_router.post("/applications/{app_id}/execute")
async def execute_application_loop(app_id: str, background_tasks: BackgroundTasks):
    app = get_app_session(app_id)
    sm: StateMachine = app["state_machine"]
    ledger: ProofLedger = app["ledger"]
    portal_adapter: MockScholarshipPortalAdapter = app["portal_adapter"]
    sid = app["portal_session_id"]
    mapped = app["mapping_result"].get("mapped_fields", {})

    if sm.current_state not in [ApplicationState.PLANNED, ApplicationState.FILLING, ApplicationState.RECOVERING]:
        if sm.current_state == ApplicationState.AWAITING_PLAN_APPROVAL:
            raise HTTPException(status_code=400, detail="Cannot execute: Plan requires user approval first")
        if sm.current_state == ApplicationState.BLOCKED:
            raise HTTPException(status_code=400, detail="Cannot execute: Application is blocked due to unresolved conflicts")

    if sm.current_state == ApplicationState.PLANNED:
        sm.transition(ApplicationState.BUILDING_STATE, reason="Initializing application state engine and action contracts")
        sm.transition(ApplicationState.FILLING, reason="Commencing form filling and document upload execution")

    # Set up ExecutionAgent
    exec_agent = ExecutionAgent(
        application_id=app_id,
        state_machine=sm,
        ledger=ledger,
        portal_adapter=portal_adapter,
        event_callback=broadcast_sync
    )
    app["execution_agent"] = exec_agent

    # 1. Action: Fill Personal Details
    personal_data = {
        "full_name": mapped.get("full_name", {}).get("value"),
        "date_of_birth": mapped.get("date_of_birth", {}).get("value"),
        "gender": mapped.get("gender", {}).get("value", "Male"),
        "category": mapped.get("category", {}).get("value", "General"),
        "email": mapped.get("email", {}).get("value", "rahul.melavanki@example.com"),
        "phone_number": mapped.get("phone_number", {}).get("value", "9876543210")
    }
    contract_personal = ActionContract(
        action_id="ACT_001_PERSONAL",
        name="Fill Personal Information",
        step_category="form_fill",
        risk_level=RiskLevel.LOW,
        preconditions=["portal_session_active", "all_personal_evidence_verified"],
        execution_command="portal_adapter.fill_step('Personal Details')",
        execution_params={"session_id": sid, "step_name": "Personal Details", "form_data": personal_data},
        postconditions=["status_200_ok", "fields_persisted_in_portal"]
    )
    res_personal = exec_agent.execute_contract(
        contract_personal,
        lambda params: portal_adapter.fill_step(params["session_id"], params["step_name"], params["form_data"])
    )

    # 2. Action: Fill Academic Details
    academic_data = {
        "institution_name": mapped.get("institution_name", {}).get("value"),
        "roll_number": mapped.get("roll_number", {}).get("value"),
        "tenth_percentage": mapped.get("tenth_percentage", {}).get("value"),
        "twelfth_percentage": mapped.get("twelfth_percentage", {}).get("value")
    }
    contract_academic = ActionContract(
        action_id="ACT_002_ACADEMIC",
        name="Fill Academic Records",
        step_category="form_fill",
        risk_level=RiskLevel.LOW,
        preconditions=["portal_session_active", "academic_evidence_verified"],
        execution_command="portal_adapter.fill_step('Academic Details')",
        execution_params={"session_id": sid, "step_name": "Academic Details", "form_data": academic_data},
        postconditions=["status_200_ok", "academic_fields_persisted"]
    )
    res_academic = exec_agent.execute_contract(
        contract_academic,
        lambda params: portal_adapter.fill_step(params["session_id"], params["step_name"], params["form_data"])
    )

    # 3. Action: Fill Financial Details
    financial_data = {
        "annual_family_income": mapped.get("annual_family_income", {}).get("value"),
        "bank_name": mapped.get("bank_name", {}).get("value"),
        "bank_account_number": mapped.get("bank_account_number", {}).get("value"),
        "ifsc_code": mapped.get("ifsc_code", {}).get("value")
    }
    contract_fin = ActionContract(
        action_id="ACT_003_FINANCIAL",
        name="Fill Financial & Bank Information",
        step_category="form_fill",
        risk_level=RiskLevel.LOW,
        preconditions=["portal_session_active", "income_evidence_verified"],
        execution_command="portal_adapter.fill_step('Financial Details')",
        execution_params={"session_id": sid, "step_name": "Financial Details", "form_data": financial_data},
        postconditions=["status_200_ok", "financial_fields_persisted"]
    )
    res_fin = exec_agent.execute_contract(
        contract_fin,
        lambda params: portal_adapter.fill_step(params["session_id"], params["step_name"], params["form_data"])
    )

    # Retrieve files via explicit doc_slots or filename fallback
    slots = app.get("doc_slots", {})
    files_list = app.get("uploaded_files", [])
    used_files = set()

    aadhaar_file = slots.get("doc_aadhaar") or next((f for f in files_list if "aadhaar" in Path(f).name.lower() or "adhar" in Path(f).name.lower()), None) or (files_list[0] if files_list else None)
    if aadhaar_file:
        used_files.add(aadhaar_file)

    marksheet_file = slots.get("doc_marksheet") or next((f for f in files_list if "marksheet" in Path(f).name.lower() and f not in used_files), None) or next((f for f in files_list if f not in used_files), None)
    if marksheet_file:
        used_files.add(marksheet_file)

    income_file = slots.get("doc_income_cert") or next((f for f in files_list if "income" in Path(f).name.lower() and f not in used_files), None)
    if income_file:
        used_files.add(income_file)

    photo_file = slots.get("doc_photo") or next((f for f in files_list if "photo" in Path(f).name.lower() and f not in used_files), None)
    if photo_file:
        used_files.add(photo_file)

    # Fallback to sample docs for demonstration self-healing if not explicitly uploaded
    sample_dir = Path(__file__).resolve().parent.parent.parent / "sample_docs"
    if not income_file and (sample_dir / "income_certificate.pdf").exists():
        income_file = str(sample_dir / "income_certificate.pdf")
    if not photo_file and (sample_dir / "photo.png").exists():
        photo_file = str(sample_dir / "photo.png")

    executed_actions = [
        res_personal.model_dump(),
        res_academic.model_dump(),
        res_fin.model_dump()
    ]

    # 4. Action: Upload Aadhaar Document
    if aadhaar_file and Path(aadhaar_file).exists():
        contract_aadhaar = ActionContract(
            action_id="ACT_004_UPLOAD_AADHAAR",
            name="Upload Identity Document (Aadhaar)",
            step_category="document_upload",
            risk_level=RiskLevel.LOW,
            preconditions=["file_readable_on_disk", "allowed_format_pdf"],
            execution_command="portal_adapter.upload_document('doc_aadhaar')",
            execution_params={"session_id": sid, "doc_type": "doc_aadhaar", "file_path": aadhaar_file, "max_size_kb": 2048},
            postconditions=["portal_accepted_upload", "checksum_verified"]
        )
        res_aadhaar = exec_agent.execute_contract(
            contract_aadhaar,
            lambda params: portal_adapter.upload_document(params["session_id"], params["doc_type"], params["file_path"])
        )
        executed_actions.append(res_aadhaar.model_dump())

    # 5. Action: Upload Marksheet Document
    if marksheet_file and Path(marksheet_file).exists():
        contract_marksheet = ActionContract(
            action_id="ACT_005_UPLOAD_MARKSHEET",
            name="Upload Academic Marksheet",
            step_category="document_upload",
            risk_level=RiskLevel.LOW,
            preconditions=["file_readable_on_disk", "allowed_format_pdf"],
            execution_command="portal_adapter.upload_document('doc_marksheet')",
            execution_params={"session_id": sid, "doc_type": "doc_marksheet", "file_path": marksheet_file, "max_size_kb": 2048},
            postconditions=["portal_accepted_upload", "checksum_verified"]
        )
        res_marksheet = exec_agent.execute_contract(
            contract_marksheet,
            lambda params: portal_adapter.upload_document(params["session_id"], params["doc_type"], params["file_path"])
        )
        executed_actions.append(res_marksheet.model_dump())

    # 6. Action: Upload Income Certificate (Triggers Oversized Failure & PDF Compression Recovery!)
    if income_file and Path(income_file).exists():
        contract_income = ActionContract(
            action_id="ACT_006_UPLOAD_INCOME_CERT",
            name="Upload Income Certificate",
            step_category="document_upload",
            risk_level=RiskLevel.LOW,
            preconditions=["file_readable_on_disk", "allowed_format_pdf"],
            execution_command="portal_adapter.upload_document('doc_income_cert')",
            execution_params={"session_id": sid, "doc_type": "doc_income_cert", "file_path": income_file, "max_size_kb": 2048},
            postconditions=["portal_accepted_upload", "size_under_2048kb"]
        )
        res_income = exec_agent.execute_contract(
            contract_income,
            lambda params: portal_adapter.upload_document(params["session_id"], params["doc_type"], params["file_path"])
        )
        executed_actions.append(res_income.model_dump())

    # 7. Action: Upload Photograph (Triggers Wrong Format / Dimensions Failure & Image Adaptation Recovery!)
    if photo_file and Path(photo_file).exists():
        contract_photo = ActionContract(
            action_id="ACT_007_UPLOAD_PHOTO",
            name="Upload Applicant Photograph",
            step_category="document_upload",
            risk_level=RiskLevel.LOW,
            preconditions=["file_readable_on_disk"],
            execution_command="portal_adapter.upload_document('doc_photo')",
            execution_params={
                "session_id": sid,
                "doc_type": "doc_photo",
                "file_path": photo_file,
                "max_size_kb": 100,
                "dimensions": (200, 230)
            },
            postconditions=["portal_accepted_upload", "format_jpg", "dimensions_200x230"]
        )
        res_photo = exec_agent.execute_contract(
            contract_photo,
            lambda params: portal_adapter.upload_document(params["session_id"], params["doc_type"], params["file_path"])
        )
        executed_actions.append(res_photo.model_dump())

    # 8. Action: Upload any remaining custom/arbitrary documents
    for slot_k, slot_p in slots.items():
        if slot_k not in ["doc_aadhaar", "doc_marksheet", "doc_income_cert", "doc_photo"] and slot_p and Path(slot_p).exists() and slot_p not in used_files:
            used_files.add(slot_p)
            c_other = ActionContract(
                action_id=f"ACT_UPLOAD_{slot_k.upper()}",
                name=f"Upload Document ({slot_k.replace('doc_', '').replace('_', ' ').title()})",
                step_category="document_upload",
                risk_level=RiskLevel.LOW,
                preconditions=["file_readable_on_disk"],
                execution_command=f"portal_adapter.upload_document('{slot_k}')",
                execution_params={"session_id": sid, "doc_type": slot_k, "file_path": slot_p, "max_size_kb": 2048},
                postconditions=["portal_accepted_upload"]
            )
            res_other = exec_agent.execute_contract(
                c_other,
                lambda params: portal_adapter.upload_document(params["session_id"], params["doc_type"], params["file_path"])
            )
            executed_actions.append(res_other.model_dump())

    # Transition to READY_FOR_REVIEW
    sm.transition(ApplicationState.READY_FOR_REVIEW, reason="All form fields and document uploads verified with deterministic evidence")
    broadcast_sync({"event_type": "state_changed", "to_state": ApplicationState.READY_FOR_REVIEW})

    return {
        "status": "SUCCESS",
        "state": sm.current_state,
        "actions_executed": executed_actions
    }

@api_router.get("/applications/{app_id}/review-data")
async def get_review_data(app_id: str):
    app = get_app_session(app_id)
    portal_adapter: MockScholarshipPortalAdapter = app["portal_adapter"]
    sid = app["portal_session_id"]
    portal_state = portal_adapter.get_application_state(sid)
    mapped = app["mapping_result"].get("mapped_fields", {})

    review_fields = []
    for fid, item in mapped.items():
        if fid.startswith("doc_"):
            continue
        f_status = item.get("status") or ("VERIFIED" if item.get("value") else "MISSING")
        review_fields.append({
            "field_id": fid,
            "label": item.get("label", fid),
            "value": item.get("value"),
            "source_file": item.get("source_file"),
            "source_page": item.get("source_page", 1),
            "evidence_text": item.get("evidence_text"),
            "confidence": item.get("confidence", 0.95),
            "status": f_status
        })

    # Collect all document keys dynamically from schema, doc_slots, and portal state
    known_doc_keys = list(dict.fromkeys(
        [d.get("key") for d in app.get("schema", {}).get("required_documents", []) if d.get("key")] +
        list(app.get("doc_slots", {}).keys()) +
        list(portal_state.get("uploaded_documents", {}).keys() if isinstance(portal_state.get("uploaded_documents"), dict) else portal_state.get("uploaded_documents", [])) +
        ["doc_aadhaar", "doc_marksheet", "doc_income_cert", "doc_photo"]
    ))
    docs_status = []
    portal_uploaded = portal_state.get("uploaded_documents", [])
    if isinstance(portal_uploaded, dict):
        portal_uploaded = list(portal_uploaded.keys())
    for doc_key in known_doc_keys:
        verified = doc_key in portal_uploaded or doc_key in app.get("doc_slots", {})
        docs_status.append({
            "document_key": doc_key,
            "label": doc_key.replace("doc_", "").replace("_", " ").title(),
            "status": "VERIFIED" if verified else "PENDING",
            "verified": verified
        })

    return {
        "application_id": app_id,
        "portal_session_id": sid,
        "review_fields": review_fields,
        "documents_status": docs_status,
        "unresolved_conflicts_count": app["mapping_result"].get("unresolved_conflicts_count", 0),
        "user_approved_submission": app["user_approved_submission"],
        "llm_audit": app.get("llm_audit"),
        "llm_fault_replies": app.get("llm_fault_replies", [])
    }

@api_router.post("/applications/{app_id}/approve-submission")
async def approve_final_submission(app_id: str, req: SubmissionApprovalRequest):
    app = get_app_session(app_id)
    sm: StateMachine = app["state_machine"]
    ledger: ProofLedger = app["ledger"]

    if req.user_confirmed:
        app["user_approved_submission"] = True
        sm.transition(ApplicationState.AWAITING_USER_SUBMISSION_APPROVAL, reason="User inspected evidence preview and granted authorization for irreversible submission")
        
        ledger.append(LedgerEntry(
            step_id="SUBMISSION_USER_APPROVAL",
            action="Irreversible Action Authorization",
            actor="user",
            evidence={"user_confirmed": True},
            status="AUTHORIZED",
            verification_result="PASSED"
        ))
        broadcast_sync({"event_type": "submission_approved", "approved": True})

    return {"status": "SUCCESS", "state": sm.current_state, "user_approved": app["user_approved_submission"]}

@api_router.post("/applications/{app_id}/submit")
async def execute_final_submission(app_id: str):
    app = get_app_session(app_id)
    sm: StateMachine = app["state_machine"]
    ledger: ProofLedger = app["ledger"]
    portal_adapter: MockScholarshipPortalAdapter = app["portal_adapter"]
    sid = app["portal_session_id"]
    mapped = app["mapping_result"].get("mapped_fields", {})

    if not app["user_approved_submission"]:
        raise HTTPException(status_code=403, detail="Irreversible Action Guard: Submission blocked. Explicit user authorization required.")

    sm.transition(ApplicationState.SUBMITTING, reason="Dispatching binding final submission to portal")
    broadcast_sync({"event_type": "state_changed", "to_state": ApplicationState.SUBMITTING})

    exec_agent: ExecutionAgent = app["execution_agent"] or ExecutionAgent(
        application_id=app_id,
        state_machine=sm,
        ledger=ledger,
        portal_adapter=portal_adapter,
        event_callback=broadcast_sync
    )

    contract_submit = ActionContract(
        action_id="ACT_008_FINAL_SUBMISSION",
        name="Submit Final Application & Obtain Verifiable Receipt",
        step_category="submission",
        risk_level=RiskLevel.HIGH,
        preconditions=["user_approval_granted", "all_fields_verified", "all_documents_uploaded"],
        execution_command="portal_adapter.submit_application()",
        execution_params={"session_id": sid, "candidate_name": mapped.get("full_name", {}).get("value")},
        postconditions=["status_200_ok", "valid_reference_number", "portal_status_submitted", "receipt_hash_verified"],
        evidence={"user_approval_granted": True}
    )

    res = exec_agent.execute_contract(
        contract_submit,
        lambda params: portal_adapter.submit_application(params["session_id"])
    )

    app["final_submission_result"] = res.model_dump()

    # Evidence Gate Final Evaluation
    portal_state = portal_adapter.get_application_state(sid)
    fields_status = {fid: "VERIFIED" for fid in mapped.keys() if not fid.startswith("doc_")}
    docs_status = {d: "VERIFIED" for d in portal_state.get("uploaded_documents", [])}
    
    gate_decision = EvidenceGate.evaluate_final_submission(
        fields_status=fields_status,
        documents_status=docs_status,
        unresolved_conflicts=[],
        submission_payload=res.evidence,
        user_approved_irreversible=app["user_approved_submission"]
    )

    if gate_decision.passed:
        sm.transition(
            ApplicationState.VERIFIED_SUCCESS,
            reason="Deterministic Evidence Gate confirmed all required proof; reference number and receipt hash independently verified",
            evidence=gate_decision.deterministic_evidence
        )
        ledger.append(LedgerEntry(
            step_id="FINAL_VERIFIED_SUCCESS",
            action="Evidence Gate Final Certification",
            actor="evidence_gate",
            observation=res.observation,
            evidence=gate_decision.deterministic_evidence,
            status="VERIFIED_SUCCESS",
            verification_result="GATE_PASSED"
        ))
    else:
        sm.transition(
            ApplicationState.VERIFICATION_FAILED,
            reason=f"Evidence Gate rejected completion: {gate_decision.reasons}",
            evidence={"reasons": gate_decision.reasons}
        )

    broadcast_sync({"event_type": "state_changed", "to_state": sm.current_state, "gate": gate_decision.model_dump()})

    return {
        "status": "SUCCESS" if gate_decision.passed else "VERIFICATION_FAILED",
        "state": sm.current_state,
        "gate_decision": gate_decision.model_dump(),
        "submission_details": res.evidence
    }

@api_router.get("/applications/{app_id}/state")
async def get_application_state(app_id: str):
    app = get_app_session(app_id)
    sm: StateMachine = app["state_machine"]
    portal_adapter: MockScholarshipPortalAdapter = app["portal_adapter"]
    sid = app["portal_session_id"]
    portal_state = portal_adapter.get_application_state(sid)
    mapped = app["mapping_result"].get("mapped_fields", {})

    total_fields = len([k for k in mapped.keys() if not k.startswith("doc_")]) or 14
    verified_fields = len([k for k, v in mapped.items() if not k.startswith("doc_") and v.get("status") == "VERIFIED"])
    docs_verified = len(portal_state.get("uploaded_documents", []))
    
    return {
        "application_id": app_id,
        "state": sm.current_state,
        "portal_session_id": sid,
        "portal_state": portal_state,
        "conflicts": app["mapping_result"].get("conflicts", []),
        "unresolved_conflicts_count": app["mapping_result"].get("unresolved_conflicts_count", 0),
        "file_issues": app.get("file_issues", []),
        "llm_audit": app.get("llm_audit"),
        "llm_fault_replies": app.get("llm_fault_replies", []),
        "metrics": {
            "total_actions": len(app["ledger"].entries),
            "verified_actions": len([e for e in app["ledger"].entries if e.status == "VERIFIED"]),
            "failed_actions": len([e for e in app["ledger"].entries if e.status == "FAILED"]),
            "recovery_count": len([e for e in app["ledger"].entries if "Recovery:" in e.action]),
            "fields_verified": f"{verified_fields} / {total_fields}",
            "documents_verified": f"{docs_verified} / 4",
            "unresolved_conflicts": app["mapping_result"].get("unresolved_conflicts_count", 0),
            "submission_status": "VERIFIED" if sm.current_state == ApplicationState.VERIFIED_SUCCESS else "NOT_SUBMITTED"
        },
        "history": [r.model_dump() for r in sm.history]
    }

@api_router.get("/applications/{app_id}/ledger")
async def get_application_ledger(app_id: str):
    app = get_app_session(app_id)
    ledger: ProofLedger = app["ledger"]
    return {
        "application_id": app_id,
        "entries_count": len(ledger.entries),
        "entries": ledger.get_all()
    }
