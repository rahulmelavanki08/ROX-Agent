from typing import Dict, Any, List, Optional
from app.services.conflict_detector import ConflictDetector, ConflictReport

class FieldMappingRecord:
    def __init__(
        self,
        field_id: str,
        label: str,
        value: Any,
        status: str,
        source_file: Optional[str] = None,
        source_page: Optional[int] = 1,
        evidence_text: Optional[str] = None,
        confidence: float = 0.0,
        conflict_details: Optional[Dict[str, Any]] = None
    ):
        self.field_id = field_id
        self.label = label
        self.value = value
        self.status = status
        self.source_file = source_file
        self.source_page = source_page
        self.evidence_text = evidence_text
        self.confidence = confidence
        self.conflict_details = conflict_details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_id": self.field_id,
            "label": self.label,
            "value": self.value,
            "status": self.status,
            "source_file": self.source_file,
            "source_page": self.source_page,
            "evidence_text": self.evidence_text,
            "confidence": self.confidence,
            "conflict_details": self.conflict_details
        }

class MappingAgent:
    """
    Zero-Trust Field & Evidence Mapping Agent.
    Strictly forbids inferring sensitive values without machine evidence.
    """
    def map_evidence(
        self,
        schema: Dict[str, Any],
        ingested_documents: List[Dict[str, Any]],
        manual_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        manual = manual_overrides or {}
        
        # 1. Group extractions by field
        extractions_by_field: Dict[str, List[Dict[str, Any]]] = {}
        for doc in ingested_documents:
            for item in doc.get("extracted_fields", []):
                fid = item.get("field")
                if fid:
                    extractions_by_field.setdefault(fid, []).append(item)

        # 2. Detect cross-document conflicts
        conflicts = ConflictDetector.detect_conflicts(extractions_by_field)
        conflict_map = {c.field_id: c for c in conflicts}

        # 3. Map to portal schema fields
        mapped_fields: Dict[str, FieldMappingRecord] = {}
        sections = schema.get("sections", [])

        for sec in sections:
            for fld in sec.get("fields", []):
                fid = fld.get("field_id")
                label = fld.get("label", fid)
                is_file = fld.get("type") == "file"

                # If overridden by user
                if fid in manual:
                    mapped_fields[fid] = FieldMappingRecord(
                        field_id=fid,
                        label=label,
                        value=manual[fid],
                        status="VERIFIED",
                        source_file="User Direct Resolution",
                        source_page=1,
                        evidence_text="Explicit user confirmation input",
                        confidence=1.0
                    )
                    continue

                # Check conflict
                if fid in conflict_map:
                    c = conflict_map[fid]
                    mapped_fields[fid] = FieldMappingRecord(
                        field_id=fid,
                        label=label,
                        value=None,
                        status="CONFLICT",
                        conflict_details=c.model_dump(),
                        confidence=0.5
                    )
                    continue

                # Normal mapping
                candidates = extractions_by_field.get(fid, [])
                if candidates:
                    candidates = sorted(
                        candidates,
                        key=lambda c: (c.get("confidence", 0.9), len(str(c.get("value", "")))),
                        reverse=True
                    )
                    best = candidates[0]
                    conf = best.get("confidence", 0.9)
                    status = "VERIFIED" if conf >= 0.95 else "LIKELY"
                    mapped_fields[fid] = FieldMappingRecord(
                        field_id=fid,
                        label=label,
                        value=best.get("value"),
                        status=status,
                        source_file=best.get("source_file"),
                        source_page=best.get("source_page", 1),
                        evidence_text=best.get("evidence_text"),
                        confidence=conf
                    )
                else:
                    if is_file:
                        # Check if a matching document file was ingested
                        matched_doc = None
                        for doc in ingested_documents:
                            fname = doc.get("file_name", "").lower()
                            dtype = (doc.get("doc_type") or "").lower()
                            if dtype == fid.lower() or (dtype and dtype.replace("doc_", "") in fid.lower()) or fid.replace("doc_", "") in fname:
                                matched_doc = doc
                                break
                        if matched_doc:
                            mapped_fields[fid] = FieldMappingRecord(
                                field_id=fid,
                                label=label,
                                value=matched_doc["file_name"],
                                status="VERIFIED",
                                source_file=matched_doc["file_name"],
                                source_page=1,
                                evidence_text=f"Matched document file: {matched_doc['file_name']}",
                                confidence=0.98
                            )
                        else:
                            mapped_fields[fid] = FieldMappingRecord(
                                field_id=fid,
                                label=label,
                                value=None,
                                status="MISSING",
                                confidence=0.0
                            )
                    else:
                        req = fld.get("required", False)
                        mapped_fields[fid] = FieldMappingRecord(
                            field_id=fid,
                            label=label,
                            value=None,
                            status="USER_INPUT_REQUIRED" if req else "MISSING",
                            confidence=0.0
                        )

        # 4. Include all other extracted document entities dynamically so arbitrary documents are never ignored
        for fid, candidates in extractions_by_field.items():
            if fid not in mapped_fields and not fid.startswith("doc_"):
                best = sorted(
                    candidates,
                    key=lambda c: (c.get("confidence", 0.9), len(str(c.get("value", "")))),
                    reverse=True
                )[0]
                label = best.get("label") or fid.replace("_", " ").title()
                conf = best.get("confidence", 0.9)
                mapped_fields[fid] = FieldMappingRecord(
                    field_id=fid,
                    label=label,
                    value=best.get("value"),
                    status="VERIFIED" if conf >= 0.95 else "LIKELY",
                    source_file=best.get("source_file"),
                    source_page=best.get("source_page", 1),
                    evidence_text=best.get("evidence_text"),
                    confidence=conf
                )

        return {
            "mapped_fields": {k: v.to_dict() for k, v in mapped_fields.items()},
            "conflicts": [c.model_dump() for c in conflicts if c.field_id not in manual],
            "unresolved_conflicts_count": len([c for c in conflicts if c.field_id not in manual])
        }
