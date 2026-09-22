import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.services.document_engine import DocumentEngine
from app.services.llm_provider import BaseLLMProvider, get_llm_provider

class DocumentAgent:
    """
    Ingests PDF, JPG, PNG, DOCX files, extracts text, tables,
    and extracts key semantic fields with precise source provenance.
    """
    def __init__(self, llm: Optional[BaseLLMProvider] = None):
        self.llm = llm or get_llm_provider()

    def ingest_document(self, file_path: str, doc_type: Optional[str] = None) -> Dict[str, Any]:
        p = Path(file_path)
        ext = p.suffix.lower()
        fname = p.name
        
        raw_text = ""
        metadata = {}

        if ext == ".pdf":
            pdf_data = DocumentEngine.extract_text_from_pdf(file_path)
            raw_text = pdf_data["full_text"]
            metadata = {
                "page_count": pdf_data["page_count"],
                "file_size_kb": pdf_data["file_size_kb"],
                "file_type": "PDF"
            }
        elif ext in [".jpg", ".jpeg", ".png"]:
            img_data = DocumentEngine.inspect_image(file_path)
            ocr_text = DocumentEngine.extract_text_from_image(file_path)
            raw_text = ocr_text if ocr_text else f"Image file: {fname}. Dimensions: {img_data['width']}x{img_data['height']}, format: {img_data['format']}"
            metadata = {
                "dimensions": (img_data["width"], img_data["height"]),
                "format": img_data["format"],
                "file_size_kb": img_data["file_size_kb"],
                "file_type": "IMAGE",
                "ocr_performed": bool(ocr_text)
            }
        elif ext in [".docx"]:
            docx_data = DocumentEngine.extract_text_from_docx(file_path)
            raw_text = docx_data["full_text"]
            metadata = {
                "file_size_kb": docx_data["file_size_kb"],
                "file_type": "DOCX"
            }
        else:
            raw_text = f"Generic file: {fname}"
            metadata = {"file_size_kb": round(os.path.getsize(file_path) / 1024.0, 2), "file_type": ext}

        # Extract semantic fields with provenance
        extracted_fields = self.llm.extract_document_fields(doc_text=raw_text, filename=fname, doc_type=doc_type)

        return {
            "file_name": fname,
            "doc_type": doc_type,
            "file_path": str(p.resolve()),
            "metadata": metadata,
            "raw_text_snippet": raw_text[:300] if raw_text else "",
            "extracted_fields": extracted_fields
        }
