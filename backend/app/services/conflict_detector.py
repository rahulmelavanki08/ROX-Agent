import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ConflictCandidate(BaseModel):
    value: str
    source_file: str
    source_page: int = 1
    evidence_text: str = ""
    confidence: float = 1.0

class ConflictReport(BaseModel):
    field_id: str
    field_label: str
    candidates: List[ConflictCandidate]
    status: str = "UNRESOLVED"  # UNRESOLVED, RESOLVED
    resolved_value: Optional[str] = None
    resolution_source: Optional[str] = None
    resolution_note: Optional[str] = None
    blocking_reason: str

class ConflictDetector:
    CRITICAL_FIELDS = {
        "date_of_birth": "Date of Birth",
        "full_name": "Full Name",
        "gender": "Gender",
        "category": "Social Category",
        "annual_family_income": "Annual Family Income",
        "bank_account_number": "Bank Account Number"
    }

    @staticmethod
    def normalize_for_comparison(field_id: str, val: Any) -> str:
        s = str(val or "").strip().lower()
        if field_id == "full_name":
            # Remove prefixes/honorifics and periods
            s = re.sub(r'\b(kumar|kumari|shri|sri|mr|mrs|ms|smt|dr)\b', '', s, flags=re.IGNORECASE)
            s = re.sub(r'[\.,\-_/\(\)]', ' ', s)
            return " ".join(s.split())
        elif field_id == "date_of_birth":
            # Standardize date separators to /
            s = re.sub(r'[\.\-_]', '/', s)
            parts = s.split('/')
            if len(parts) == 3:
                d, m, y = parts[0].zfill(2), parts[1].zfill(2), parts[2]
                return f"{d}/{m}/{y}"
            return s
        elif field_id == "annual_family_income":
            # Extract pure digits
            digits = re.sub(r'[^\d]', '', s.split('.')[0])
            return digits if digits else s
        elif field_id == "gender":
            return s[0] if s else ""
        elif field_id == "category":
            if "ii-b" in s or "iib" in s or "1 1 (b)" in s:
                return "obc_2b"
            elif "obc" in s:
                return "obc"
            elif "sc" in s:
                return "sc"
            elif "st" in s:
                return "st"
            elif "gen" in s:
                return "general"
            return s
        return re.sub(r'[\s\.\-_/]', '', s)

    @classmethod
    def detect_conflicts(cls, extractions_by_field: Dict[str, List[Dict[str, Any]]]) -> List[ConflictReport]:
        from difflib import SequenceMatcher
        conflicts = []
        for field_id, label in cls.CRITICAL_FIELDS.items():
            records = extractions_by_field.get(field_id, [])
            if len(records) > 1:
                candidates = []
                norm_records = []
                for r in records:
                    raw_val = str(r.get("value", "")).strip()
                    norm_val = cls.normalize_for_comparison(field_id, raw_val)
                    candidates.append(ConflictCandidate(
                        value=raw_val,
                        source_file=r.get("source_file", "unknown"),
                        source_page=r.get("source_page", 1),
                        evidence_text=r.get("evidence_text", ""),
                        confidence=r.get("confidence", 0.9)
                    ))
                    norm_records.append(norm_val)

                has_conflict = False
                base_norm = norm_records[0]
                for other_norm in norm_records[1:]:
                    if field_id == "full_name":
                        # If names are high similarity (ratio >= 0.75) or one word list is subset of other,
                        # treat as slight OCR noise or initial expansion of same individual.
                        words_base = set(base_norm.split())
                        words_other = set(other_norm.split())
                        is_subset = words_base.issubset(words_other) or words_other.issubset(words_base)
                        sim = SequenceMatcher(None, base_norm, other_norm).ratio()
                        if not is_subset and sim < 0.75:
                            has_conflict = True
                            break
                    else:
                        if base_norm != other_norm:
                            has_conflict = True
                            break

                if has_conflict:
                    distinct_sources = [f"'{c.value}' in {c.source_file}" for c in candidates]
                    distinct_sources_summary = " vs ".join(distinct_sources[:2])
                    blocking_reason = (
                        f"Identity Mismatch detected: {distinct_sources_summary}. "
                        f"These documents contain conflicting records for critical field '{label}'. "
                        f"Under Zero-Trust policy, ROX blocks automatic progression until you select the correct identity."
                    )
                    conflicts.append(ConflictReport(
                        field_id=field_id,
                        field_label=label,
                        candidates=candidates,
                        blocking_reason=blocking_reason
                    ))
        return conflicts
