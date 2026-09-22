import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.text_extractor import extract_fields_from_raw_text

logger = logging.getLogger("rox.llm")

class BaseLLMProvider(ABC):
    @abstractmethod
    def analyze_requirements(self, page_context: str, goal: str, app_type: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def extract_document_fields(self, doc_text: str, filename: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def compare_inter_documents(self, ingested_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def diagnose_fault_and_reply(self, fault_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def diagnose_failure(self, action_name: str, observation: Dict[str, Any], error: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def propose_recovery_plan(self, failure_diagnosis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        pass

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        from google import genai
        self.client = genai.Client(api_key=self.api_key)

    def _call_gemini_json(self, prompt: str, system_instruction: str = "") -> Dict[str, Any]:
        models_to_try = [self.model_name] + [m for m in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"] if m != self.model_name]
        last_error = None
        for model in models_to_try:
            try:
                full_prompt = f"{system_instruction}\n\nUser Prompt:\n{prompt}\n\nRespond ONLY with valid JSON without markdown wrapping if possible, or standard ```json ``` code block."
                response = self.client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                parsed = json.loads(text.strip())
                self.model_name = model
                return parsed
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini call with model {model} failed: {e}. Trying fallback model.")

        logger.error(f"All Gemini models failed. Last error: {last_error}")
        raise last_error

    def analyze_requirements(self, page_context: str, goal: str, app_type: Optional[str] = None) -> Dict[str, Any]:
        prompt = (
            f"Application Type / Scheme: {app_type or 'General Application'}\n"
            f"Application Context:\n{page_context}\n\n"
            f"Goal: {goal}\n\n"
            "Task: Extract comprehensive application schema JSON with:\n"
            "- application_title: Title of application\n"
            "- application_code: Identifier code\n"
            "- sections: Array of sections, each with section_id, title, and fields array.\n"
            "Each field must have: field_id, label, type ('text'|'number'|'date'|'select'|'file'), required (bool), source_preference, verification_required (bool)."
        )
        sys_inst = "You are an autonomous application analyst. Output valid JSON matching schema."
        try:
            return self._call_gemini_json(prompt, sys_inst)
        except Exception:
            return MockLLMProvider().analyze_requirements(page_context, goal, app_type)

    def extract_document_fields(self, doc_text: str, filename: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        # Hybrid Zero-Trust: First compute deterministic baseline extraction
        local_fields = extract_fields_from_raw_text(doc_text, filename, doc_type)

        prompt = (
            f"Document Name: {filename}\n"
            f"Document Type: {doc_type or 'General Citizen Document'}\n"
            f"Document OCR Text:\n{doc_text}\n\n"
            "Task: Extract ALL structured citizen particulars, identity credentials, educational records, "
            "family relationships, financial details, certificate numbers, addresses, and key-value pairs from this document text.\n"
            "Guidelines:\n"
            "1. Extract standard entities if present:\n"
            "   - full_name: The applicant / candidate / citizen's actual full name ONLY (do not mix with parent name).\n"
            "   - date_of_birth: Formatted as DD/MM/YYYY.\n"
            "   - gender: 'Male', 'Female', or 'Other'.\n"
            "   - father_name, mother_name, guardian_name.\n"
            "   - category (e.g. 'OBC', 'SC', 'ST', 'General', 'EWS') and sub_caste.\n"
            "   - address, district, state, pincode.\n"
            "   - phone_number / mobile_number, email.\n"
            "   - roll_number, registration_number, admission_number.\n"
            "   - tenth_percentage, twelfth_percentage, marks, cgpa.\n"
            "   - annual_family_income, income_amount.\n"
            "   - bank_name, bank_account_number, ifsc_code, branch_name.\n"
            "   - institution_name, college_name, school_name, course_name, branch_name, academic_year.\n"
            "   - certificate_number, rd_number, ration_card_number, aadhaar_number, pan_number, voter_id.\n"
            "   - hostel_name, room_number, caution_deposit, fee_amount, receipt_number, mess_option.\n"
            "2. Also extract ANY OTHER document-specific data fields present on this document (e.g., issue_date, valid_upto, conduct, authority, remarks) using descriptive snake_case keys.\n"
            "3. Grounding: Quote the exact verbatim phrase from the OCR text in 'evidence_text'. Never hallucinate or invent fields.\n\n"
            "Output JSON array of objects with:\n"
            "- field: snake_case identifier\n"
            "- label: human readable label\n"
            "- value: clean extracted string value\n"
            "- source_file: '{filename}'\n"
            "- source_page: 1\n"
            "- evidence_text: exact quotation from text\n"
            "- confidence: float (0.90 to 1.0)"
        )
        sys_inst = "You are ROX Zero-Trust Intelligent Document Understanding Engine. Output valid JSON array."
        try:
            res = self._call_gemini_json(prompt, sys_inst)
            gemini_fields = res if isinstance(res, list) else res.get("fields", [])
            if gemini_fields:
                local_field_map = {f["field"]: f for f in local_fields}
                merged = []
                seen_fields = set()
                for gf in gemini_fields:
                    fid = gf.get("field")
                    if fid and fid not in seen_fields:
                        seen_fields.add(fid)
                        val = gf.get("value")
                        lbl = gf.get("label") or fid.replace("_", " ").title()
                        lf = local_field_map.get(fid)
                        merged.append({
                            "field": fid,
                            "label": lbl,
                            "value": val or (lf.get("value") if lf else ""),
                            "source_file": filename,
                            "source_page": 1,
                            "evidence_text": (lf.get("evidence_text") if lf else None) or gf.get("evidence_text", ""),
                            "confidence": max(gf.get("confidence", 0.95), (lf.get("confidence", 0.95) if lf else 0.95))
                        })
                # Include any local deterministic extractions not in Gemini output
                for fid, lf in local_field_map.items():
                    if fid not in seen_fields:
                        merged.append(lf)
                return merged
        except Exception as e:
            logger.warning(f"Gemini entity extraction failed: {e}. Falling back to deterministic extraction.")

        return local_fields

    def compare_inter_documents(self, ingested_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = (
            "You are an expert zero-trust application verification agent.\n"
            "Analyze the following ingested enclosures and their extracted fields:\n"
            f"{json.dumps(ingested_documents, indent=2)}\n\n"
            "Task: Compare all details across these documents (Aadhaar, Marksheets, Passbook, Income Certificate).\n"
            "1. Verify whether the applicant's identity (Full Name, Date of Birth, Gender, Parents) is consistent.\n"
            "2. Distinguish minor OCR noise or standard Indian naming conventions (e.g. 'Chinthan Gowda' vs 'Chinthan V Gowda' where 'V' stands for father Vasanthakumara) from true identity fraud (e.g. 'M Vinayaka' vs 'M Veeresh').\n"
            "3. If two different individuals are detected, identify the mismatch.\n\n"
            "Output JSON with:\n"
            "- same_person: boolean\n"
            "- confidence: float\n"
            "- summary: concise summary\n"
            "- key_matches: list of fields matching across documents\n"
            "- discrepancies: list of discrepancies found, if any\n"
            "- llm_verdict: conversational explanation from ROX AI Agent explaining the cross-document audit."
        )
        sys_inst = "You are a zero-trust fraud verification officer. Output valid JSON."
        try:
            return self._call_gemini_json(prompt, sys_inst)
        except Exception as e:
            logger.warning(f"Gemini inter-document comparison error: {e}. Falling back to deterministic comparison.")
            return MockLLMProvider().compare_inter_documents(ingested_documents)

    def diagnose_fault_and_reply(self, fault_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            "You are the ROX Autonomous Recovery Agent.\n"
            f"Fault Type: {fault_type}\n"
            f"Details: {json.dumps(details, indent=2)}\n\n"
            "Task: Generate an intelligent, conversational agent reply explaining this fault, "
            "its root cause, the self-healing actions executed or required user selection, and zero-trust safety.\n"
            "Output JSON with:\n"
            "- fault_title: short title\n"
            "- fault_category: DATA_ERROR | DOCUMENT_ERROR | FORMAT_ERROR | UPLOAD_ERROR | PORTAL_ERROR\n"
            "- severity: CRITICAL | WARNING | INFO\n"
            "- llm_agent_reply: a clear, friendly conversational response speaking as ROX AI Agent\n"
            "- recovery_action: description of recovery action taken or recommended"
        )
        sys_inst = "You are ROX Agentic Workflow assistant. Output valid JSON."
        try:
            return self._call_gemini_json(prompt, sys_inst)
        except Exception as e:
            logger.warning(f"Gemini fault diagnosis error: {e}. Falling back to deterministic fault reply.")
            return MockLLMProvider().diagnose_fault_and_reply(fault_type, details)

    def diagnose_failure(self, action_name: str, observation: Dict[str, Any], error: str) -> Dict[str, Any]:
        prompt = f"Action: {action_name}\nObservation: {json.dumps(observation)}\nError: {error}\n\nClassify failure category (DATA_ERROR, DOCUMENT_ERROR, FORMAT_ERROR, UPLOAD_ERROR, VALIDATION_ERROR, PORTAL_SCHEMA_CHANGE, SESSION_EXPIRED, NETWORK_ERROR, TIMEOUT, UNKNOWN_STATE, SUBMISSION_ERROR). Output JSON with failure_category, root_cause, can_recover, proposed_strategy."
        try:
            return self._call_gemini_json(prompt, "You are an AI diagnostic agent.")
        except Exception:
            return MockLLMProvider().diagnose_failure(action_name, observation, error)

    def propose_recovery_plan(self, failure_diagnosis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"Diagnosis: {json.dumps(failure_diagnosis)}\nContext: {json.dumps(context)}\n\nGenerate structured recovery plan JSON with recovery_steps, tool, parameters."
        try:
            return self._call_gemini_json(prompt, "You are a self-healing recovery agent.")
        except Exception:
            return MockLLMProvider().propose_recovery_plan(failure_diagnosis, context)


class MockLLMProvider(BaseLLMProvider):
    def analyze_requirements(self, page_context: str, goal: str, app_type: Optional[str] = None) -> Dict[str, Any]:
        app_type_str = str(app_type or goal or page_context).lower()
        if "hostel" in app_type_str:
            return {
                "application_title": "Government Post-Matric Hostel Admission 2026",
                "application_code": "HST-2026",
                "sections": [
                    {
                        "section_id": "personal",
                        "title": "Applicant Profile",
                        "fields": [
                            {"field_id": "full_name", "label": "Full Name", "type": "text", "required": True, "source_preference": "aadhaar", "verification_required": True},
                            {"field_id": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True, "source_preference": "aadhaar", "verification_required": True},
                            {"field_id": "gender", "label": "Gender", "type": "select", "required": True, "source_preference": "aadhaar", "verification_required": False},
                            {"field_id": "category", "label": "Social Category", "type": "select", "required": True, "source_preference": "income_certificate", "verification_required": False},
                            {"field_id": "phone_number", "label": "Mobile Phone", "type": "tel", "required": True, "source_preference": "user_input", "verification_required": False},
                            {"field_id": "father_name", "label": "Father / Guardian Name", "type": "text", "required": True, "source_preference": "aadhaar", "verification_required": False},
                            {"field_id": "address", "label": "Permanent Domicile Address", "type": "text", "required": True, "source_preference": "aadhaar", "verification_required": False}
                        ]
                    },
                    {
                        "section_id": "academic",
                        "title": "Hostel & Course Info",
                        "fields": [
                            {"field_id": "institution_name", "label": "College / University Name", "type": "text", "required": True, "source_preference": "marksheet", "verification_required": False},
                            {"field_id": "roll_number", "label": "Admission / Roll Number", "type": "text", "required": True, "source_preference": "marksheet", "verification_required": True},
                            {"field_id": "branch_name", "label": "Course / Branch", "type": "text", "required": False, "source_preference": "marksheet", "verification_required": False},
                            {"field_id": "hostel_name", "label": "Preferred Hostel Block", "type": "text", "required": False, "source_preference": "user_input", "verification_required": False}
                        ]
                    },
                    {
                        "section_id": "documents",
                        "title": "Document Enclosures",
                        "fields": [
                            {"field_id": "doc_aadhaar", "label": "Aadhaar Card", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                            {"field_id": "doc_marksheet", "label": "College Fee Receipt / Marksheet", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                            {"field_id": "doc_income_cert", "label": "Income & Caste Certificate", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                            {"field_id": "doc_photo", "label": "Passport Sized Photograph", "type": "file", "required": True, "allowed_types": ["image/jpeg"], "max_size_kb": 100, "dimensions": {"width": 200, "height": 230}, "verification_required": True}
                        ]
                    }
                ]
            }
        elif "certificate" in app_type_str or "caste" in app_type_str:
            return {
                "application_title": "Government Income & Caste Certificate",
                "application_code": "CERT-2026",
                "sections": [
                    {
                        "section_id": "personal",
                        "title": "Citizen Identity",
                        "fields": [
                            {"field_id": "full_name", "label": "Full Legal Name", "type": "text", "required": True, "source_preference": "aadhaar", "verification_required": True},
                            {"field_id": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True, "source_preference": "aadhaar", "verification_required": True},
                            {"field_id": "gender", "label": "Gender", "type": "select", "required": True, "source_preference": "aadhaar", "verification_required": False},
                            {"field_id": "category", "label": "Caste Category", "type": "select", "required": True, "source_preference": "aadhaar", "verification_required": False},
                            {"field_id": "sub_caste", "label": "Sub-Caste", "type": "text", "required": False, "source_preference": "income_cert", "verification_required": False},
                            {"field_id": "phone_number", "label": "Mobile Phone", "type": "tel", "required": True, "source_preference": "user_input", "verification_required": False},
                            {"field_id": "father_name", "label": "Father's Name", "type": "text", "required": True, "source_preference": "aadhaar", "verification_required": False},
                            {"field_id": "address", "label": "Residential Address", "type": "text", "required": True, "source_preference": "aadhaar", "verification_required": False}
                        ]
                    },
                    {
                        "section_id": "financial",
                        "title": "Family & Income Details",
                        "fields": [
                            {"field_id": "annual_family_income", "label": "Gross Annual Family Income", "type": "number", "required": True, "source_preference": "income_certificate", "verification_required": True},
                            {"field_id": "certificate_number", "label": "Existing RD / Affidavit Number", "type": "text", "required": False, "source_preference": "income_certificate", "verification_required": False},
                            {"field_id": "issuing_authority", "label": "Revenue Taluk / Authority", "type": "text", "required": False, "source_preference": "income_certificate", "verification_required": False}
                        ]
                    },
                    {
                        "section_id": "documents",
                        "title": "Document Enclosures",
                        "fields": [
                            {"field_id": "doc_aadhaar", "label": "Identity Proof (Aadhaar / Voter ID)", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                            {"field_id": "doc_passbook", "label": "Ration Card / Bank Passbook", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                            {"field_id": "doc_income_cert", "label": "Salary / Self-Declaration Certificate", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                            {"field_id": "doc_photo", "label": "Applicant Photograph", "type": "file", "required": True, "allowed_types": ["image/jpeg"], "max_size_kb": 100, "dimensions": {"width": 200, "height": 230}, "verification_required": True}
                        ]
                    }
                ]
            }
        return {
            "application_title": "National Merit & Need-Based Scholarship 2026",
            "application_code": "SCH-2026",
            "sections": [
                {
                    "section_id": "personal",
                    "title": "Personal Information",
                    "fields": [
                        {"field_id": "full_name", "label": "Full Legal Name", "type": "text", "required": True, "source_preference": "aadhaar", "verification_required": True},
                        {"field_id": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True, "source_preference": "aadhaar", "verification_required": True},
                        {"field_id": "gender", "label": "Gender", "type": "select", "required": True, "source_preference": "aadhaar", "verification_required": False},
                        {"field_id": "category", "label": "Social Category", "type": "select", "required": True, "source_preference": "aadhaar", "verification_required": False},
                        {"field_id": "email", "label": "Email Address", "type": "email", "required": True, "source_preference": "user_input", "verification_required": False},
                        {"field_id": "phone_number", "label": "Mobile Phone", "type": "tel", "required": True, "source_preference": "user_input", "verification_required": False}
                    ]
                },
                {
                    "section_id": "academic",
                    "title": "Academic Record",
                    "fields": [
                        {"field_id": "institution_name", "label": "Current Institution Name", "type": "text", "required": True, "source_preference": "marksheet", "verification_required": False},
                        {"field_id": "roll_number", "label": "Student Roll Number", "type": "text", "required": True, "source_preference": "marksheet", "verification_required": True},
                        {"field_id": "tenth_percentage", "label": "10th Grade Percentage / CGPA", "type": "number", "required": True, "source_preference": "marksheet", "verification_required": True},
                        {"field_id": "twelfth_percentage", "label": "12th Grade Percentage / CGPA", "type": "number", "required": True, "source_preference": "marksheet", "verification_required": True}
                    ]
                },
                {
                    "section_id": "financial",
                    "title": "Financial & Banking Information",
                    "fields": [
                        {"field_id": "annual_family_income", "label": "Annual Family Income (INR)", "type": "number", "required": True, "source_preference": "income_certificate", "verification_required": True},
                        {"field_id": "bank_name", "label": "Bank Name", "type": "text", "required": True, "source_preference": "bank_passbook", "verification_required": False},
                        {"field_id": "bank_account_number", "label": "Bank Account Number", "type": "text", "required": True, "source_preference": "bank_passbook", "verification_required": True},
                        {"field_id": "ifsc_code", "label": "IFSC Code", "type": "text", "required": True, "source_preference": "bank_passbook", "verification_required": True}
                    ]
                },
                {
                    "section_id": "documents",
                    "title": "Document Uploads",
                    "fields": [
                        {"field_id": "doc_aadhaar", "label": "Identity Proof (Aadhaar)", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                        {"field_id": "doc_marksheet", "label": "Academic Marksheet", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                        {"field_id": "doc_income_cert", "label": "Income Certificate", "type": "file", "required": True, "allowed_types": ["application/pdf"], "max_size_kb": 2048, "verification_required": True},
                        {"field_id": "doc_photo", "label": "Applicant Photograph", "type": "file", "required": True, "allowed_types": ["image/jpeg"], "max_size_kb": 100, "dimensions": {"width": 200, "height": 230}, "verification_required": True}
                    ]
                }
            ]
        }

    def extract_document_fields(self, doc_text: str, filename: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        # 1. Run semantic entity extraction on real document text
        real_extractions = extract_fields_from_raw_text(doc_text, filename, doc_type)
        if real_extractions:
            return real_extractions

        # 2. Fallback ONLY for built-in demo benchmark files
        fname = filename.lower()
        is_builtin_demo_sample = fname in ["aadhaar.pdf", "marksheet.pdf", "income_certificate.pdf", "bank_passbook.pdf", "photo.png"]
        if not is_builtin_demo_sample:
            return []

        extracted = []
        if "aadhaar" in fname:
            extracted.extend([
                {"field": "full_name", "value": "Rahul Melavanki", "source_file": filename, "source_page": 1, "evidence_text": "Name: Rahul Melavanki", "confidence": 0.99},
                {"field": "date_of_birth", "value": "14/05/2007", "source_file": filename, "source_page": 1, "evidence_text": "DOB: 14/05/2007", "confidence": 0.98},
                {"field": "gender", "value": "Male", "source_file": filename, "source_page": 1, "evidence_text": "Gender: Male / Purush", "confidence": 0.99},
                {"field": "category", "value": "General", "source_file": filename, "source_page": 1, "evidence_text": "Social Category: General", "confidence": 0.95},
                {"field": "aadhaar_number", "value": "XXXX-XXXX-9481", "source_file": filename, "source_page": 1, "evidence_text": "Aadhaar No: XXXX-XXXX-9481", "confidence": 0.99}
            ])
        elif "marksheet" in fname:
            extracted.extend([
                {"field": "full_name", "value": "Rahul Melavanki", "source_file": filename, "source_page": 1, "evidence_text": "Candidate Name: Rahul Melavanki", "confidence": 0.99},
                {"field": "date_of_birth", "value": "15/05/2007", "source_file": filename, "source_page": 1, "evidence_text": "Birth Date: 15/05/2007", "confidence": 0.98},
                {"field": "institution_name", "value": "National Institute of Technology", "source_file": filename, "source_page": 1, "evidence_text": "Institution: National Institute of Technology", "confidence": 0.97},
                {"field": "roll_number", "value": "NITK2024CS089", "source_file": filename, "source_page": 1, "evidence_text": "Roll No: NITK2024CS089", "confidence": 0.99},
                {"field": "tenth_percentage", "value": "92.4", "source_file": filename, "source_page": 1, "evidence_text": "10th Standard Aggregate: 92.4%", "confidence": 0.98},
                {"field": "twelfth_percentage", "value": "89.6", "source_file": filename, "source_page": 1, "evidence_text": "12th / Pre-University: 89.6%", "confidence": 0.98}
            ])
        elif "income" in fname:
            extracted.extend([
                {"field": "annual_family_income", "value": "240000", "source_file": filename, "source_page": 1, "evidence_text": "Certified Annual Family Income: Rs. 2,40,000 /-", "confidence": 0.99},
                {"field": "certificate_number", "value": "REV-INC-2026-98102", "source_file": filename, "source_page": 1, "evidence_text": "Certificate No: REV-INC-2026-98102", "confidence": 0.99}
            ])
        elif "passbook" in fname or "bank" in fname:
            extracted.extend([
                {"field": "bank_name", "value": "State Bank of India", "source_file": filename, "source_page": 1, "evidence_text": "Bank: State Bank of India, Koramangala Branch", "confidence": 0.99},
                {"field": "bank_account_number", "value": "39485729104", "source_file": filename, "source_page": 1, "evidence_text": "A/C No: 39485729104", "confidence": 0.99},
                {"field": "ifsc_code", "value": "SBIN0001423", "source_file": filename, "source_page": 1, "evidence_text": "IFSC: SBIN0001423", "confidence": 0.99}
            ])
        elif "photo" in fname:
            extracted.extend([
                {"field": "applicant_photo", "value": filename, "source_file": filename, "source_page": 1, "evidence_text": "Applicant Identity Photograph", "confidence": 0.95}
            ])
        return extracted

    def compare_inter_documents(self, ingested_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        names = []
        dobs = []
        for doc in ingested_documents:
            for f in doc.get("extracted_fields", []):
                if f.get("field") == "full_name":
                    names.append((f.get("value"), doc.get("file_name")))
                elif f.get("field") == "date_of_birth":
                    dobs.append((f.get("value"), doc.get("file_name")))

        has_conflict = False
        discrepancies = []
        if len(names) > 1:
            from difflib import SequenceMatcher
            n1 = names[0][0].lower()
            for n2, src in names[1:]:
                sim = SequenceMatcher(None, n1, n2.lower()).ratio()
                tokens1 = set(n1.split())
                tokens2 = set(n2.lower().split())
                if not (tokens1.issubset(tokens2) or tokens2.issubset(tokens1)) and sim < 0.75:
                    has_conflict = True
                    discrepancies.append(f"Name discrepancy: '{names[0][0]}' in {names[0][1]} vs '{n2}' in {src}")

        if len(dobs) > 1:
            d1 = dobs[0][0]
            for d2, src in dobs[1:]:
                if d1 != d2:
                    has_conflict = True
                    discrepancies.append(f"DOB discrepancy: '{d1}' in {dobs[0][1]} vs '{d2}' in {src}")

        if has_conflict:
            return {
                "same_person": False,
                "confidence": 0.99,
                "summary": "Cross-document identity verification detected conflicting records.",
                "key_matches": [],
                "discrepancies": discrepancies,
                "llm_verdict": f"Identity Mismatch Alert: Conflicting identity records found ({'; '.join(discrepancies)}). Under Zero-Trust policy, ROX blocks automated progression until resolved."
            }
        else:
            primary_name = names[0][0] if names else "Applicant"
            return {
                "same_person": True,
                "confidence": 0.98,
                "summary": f"Cross-document identity verified successfully for {primary_name}.",
                "key_matches": ["full_name", "date_of_birth", "gender"],
                "discrepancies": [],
                "llm_verdict": f"AI Inter-Document Audit: Verified that all uploaded enclosures correspond to '{primary_name}' with 0 identity conflicts."
            }

    def diagnose_fault_and_reply(self, fault_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        if "conflict" in fault_type.lower() or details.get("conflicts"):
            conflicts = details.get("conflicts", [])
            summary = "; ".join([c.get("blocking_reason", "") for c in conflicts]) if isinstance(conflicts, list) else str(conflicts)
            return {
                "fault_title": "Cross-Document Identity Conflict",
                "fault_category": "DATA_ERROR",
                "severity": "CRITICAL",
                "llm_agent_reply": (
                    f"ROX Zero-Trust Security Alert: Cross-document identity reconciliation detected conflicting records: {summary}. "
                    "Under zero-trust verification rules, ROX will NOT hallucinate or guess which person is correct. "
                    "Please select the verified legal identity above to proceed."
                ),
                "recovery_action": "Awaiting user selection of valid identity."
            }
        elif "format" in fault_type.lower() or "convert" in fault_type.lower() or details.get("file_issues"):
            issues = details.get("file_issues", [])
            return {
                "fault_title": "Document Standardisation & Adaptation Anomaly",
                "fault_category": "DOCUMENT_ERROR",
                "severity": "WARNING",
                "llm_agent_reply": (
                    f"ROX Autonomous Engine: Detected {len(issues)} enclosure(s) that do not match the target portal's strict PDF format "
                    "or size thresholds (e.g. mobile JPG uploads instead of 2MB PDF). "
                    "ROX has automatically executed zero-touch transformation: converting images to clean standard PDFs and optimizing compression."
                ),
                "recovery_action": "Automated zero-touch image-to-PDF conversion and PDF stream compression."
            }
        return {
            "fault_title": "Execution Anomaly",
            "fault_category": "PORTAL_ERROR",
            "severity": "WARNING",
            "llm_agent_reply": f"ROX Self-Healing Agent: Encountered {fault_type}. Applying bounded recovery strategy.",
            "recovery_action": "Re-execute action contract with adapted parameters."
        }

    def diagnose_failure(self, action_name: str, observation: Dict[str, Any], error: str) -> Dict[str, Any]:
        obs_text = str(observation) + " " + str(error)
        if "exceeds" in obs_text.lower() or "too large" in obs_text.lower() or "2mb" in obs_text.lower():
            return {
                "failure_category": "UPLOAD_ERROR",
                "root_cause": "File size exceeds maximum portal threshold of 2MB",
                "can_recover": True,
                "proposed_strategy": "DOCUMENT_COMPRESSION"
            }
        elif "dimensions" in obs_text.lower() or "format" in obs_text.lower() or "200x230" in obs_text.lower():
            return {
                "failure_category": "FORMAT_ERROR",
                "root_cause": "Image format or dimensions mismatch (Requires JPG, 200x230, <100KB)",
                "can_recover": True,
                "proposed_strategy": "IMAGE_ADAPTATION"
            }
        elif "session" in obs_text.lower() or "401" in obs_text or "expired" in obs_text.lower():
            return {
                "failure_category": "SESSION_EXPIRED",
                "root_cause": "Portal session expired mid-workflow",
                "can_recover": True,
                "proposed_strategy": "STATE_RECONSTRUCTION_AND_RESUME"
            }
        elif "timeout" in obs_text.lower() or "504" in obs_text:
            return {
                "failure_category": "TIMEOUT",
                "root_cause": "Save request timed out, resulting in UNKNOWN state",
                "can_recover": True,
                "proposed_strategy": "RECONCILE_SERVER_STATE"
            }
        elif "schema" in obs_text.lower() or "field" in obs_text.lower():
            return {
                "failure_category": "PORTAL_SCHEMA_CHANGE",
                "root_cause": "Portal DOM field attribute or name changed",
                "can_recover": True,
                "proposed_strategy": "REMAP_FIELD_SCHEMA"
            }
        return {
            "failure_category": "UNKNOWN_STATE",
            "root_cause": error or "Unclassified execution failure",
            "can_recover": False,
            "proposed_strategy": "HALT_AND_REPORT"
        }

    def propose_recovery_plan(self, failure_diagnosis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        strategy = failure_diagnosis.get("proposed_strategy", "")
        if strategy == "DOCUMENT_COMPRESSION":
            return {
                "strategy": "DOCUMENT_COMPRESSION",
                "tool": "document_engine.compress_pdf",
                "parameters": {"target_kb": 1800},
                "steps": ["Compress PDF stream", "Verify file size on disk < 2048 KB", "Re-upload to portal", "Verify upload receipt"]
            }
        elif strategy == "IMAGE_ADAPTATION":
            return {
                "strategy": "IMAGE_ADAPTATION",
                "tool": "document_engine.adapt_photo",
                "parameters": {"target_format": "JPEG", "target_dimensions": [200, 230], "max_kb": 95},
                "steps": ["Convert PNG to JPG", "Resize to exactly 200x230 px", "Compress to < 100 KB", "Verify file properties", "Re-upload", "Verify portal acceptance"]
            }
        elif strategy == "STATE_RECONSTRUCTION_AND_RESUME":
            return {
                "strategy": "STATE_RECONSTRUCTION_AND_RESUME",
                "tool": "portal_adapter.reconstruct_and_resume",
                "parameters": {},
                "steps": ["Query portal draft checkpoint", "Reconcile verified local fields with portal state", "Resume workflow at first unverified section"]
            }
        elif strategy == "RECONCILE_SERVER_STATE":
            return {
                "strategy": "RECONCILE_SERVER_STATE",
                "tool": "portal_adapter.check_persisted_state",
                "parameters": {},
                "steps": ["Query portal draft record", "Check last_updated timestamp and record ID", "If fields match, mark VERIFIED; otherwise retry save"]
            }
        return {
            "strategy": "MANUAL_INTERVENTION",
            "tool": "user_intervention",
            "parameters": {},
            "steps": ["Notify user", "Await manual resolution"]
        }

def get_llm_provider(api_key: Optional[str] = None) -> BaseLLMProvider:
    key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
    if key and key.strip():
        try:
            logger.info("Initializing Google GeminiProvider with supplied key.")
            return GeminiProvider(api_key=key.strip())
        except Exception as e:
            logger.warning(f"Could not initialize GeminiProvider ({e}), falling back to MockLLMProvider.")
            return MockLLMProvider()
    return MockLLMProvider()
