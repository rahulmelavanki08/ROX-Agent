import re
from typing import List, Dict, Any, Optional

def extract_fields_from_raw_text(doc_text: str, filename: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
    extracted: List[Dict[str, Any]] = []
    text = doc_text or ""
    added_fields = set()

    def add(fid: str, val: Any, quote: str, conf: float = 0.98):
        if fid not in added_fields and val:
            added_fields.add(fid)
            extracted.append({
                "field": fid,
                "value": str(val).strip(),
                "source_file": filename,
                "source_page": 1,
                "evidence_text": quote.strip()[:100],
                "confidence": conf
            })

    # 1. Full Name
    name_patterns = [
        r"(?:Candidate\s+Name|Full\s+Name|Applicant\s+Name|Account\s+Holder|Name\s*/\s*Naam)\s*[:\-]?\s*([A-Za-z\s\.]{2,40})",
        r"\bName\s*[:\-]\s*([A-Za-z\s\.]{2,40})",
        r"\bSri\s+([A-Za-z\s\.]{3,35}),\s*(?:son|daughter)\s+of",
    ]
    for pat in name_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().strip(".,:-/")
            if len(val.split()) >= 1 and val.lower() not in ["of", "the", "certificate", "government", "board", "identification"]:
                add("full_name", val, m.group(0))
                break

    # 2. Date of Birth
    dob_patterns = [
        r"(?:Date\s+of\s+Birth\s*/\s*Janma\s+Dina|Date\s+of\s+Birth|Birth\s+Date|DOB|D\.O\.B\.?)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
    ]
    for pat in dob_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            norm_val = m.group(1).strip().replace("-", "/").replace(".", "/")
            add("date_of_birth", norm_val, m.group(0))
            break
    if "date_of_birth" not in added_fields:
        if "birth" in text.lower() or "dob" in text.lower() or (doc_type and "aadhaar" in doc_type):
            m = re.search(r"\b(\d{2}[/\-]\d{2}[/\-]\d{4})\b", text)
            if m:
                add("date_of_birth", m.group(1).replace("-", "/"), f"Birth Date: {m.group(0)}", 0.90)

    # 3. Gender
    m_gen = re.search(r"(?:Gender\s*/\s*Linga|Gender|Sex)\s*[:\-]?\s*(Male|Female|Transgender|Other)", text, re.IGNORECASE)
    if m_gen:
        add("gender", m_gen.group(1).capitalize(), m_gen.group(0))

    # 4. Social Category
    m_cat = re.search(r"(?:Social\s+Category|Category|Caste)\s*[:\-]?\s*(General|OBC|SC|ST|EWS)", text, re.IGNORECASE)
    if m_cat:
        add("category", m_cat.group(1).capitalize(), m_cat.group(0))

    # 5. Email
    m_email = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7})", text)
    if m_email:
        add("email", m_email.group(1), m_email.group(0), 0.99)

    # 6. Phone / Mobile Number
    m_phone = re.search(r"(?:Mobile|Phone|Contact|Cell)\s*(?:No\.?)?\s*[:\-]?\s*(?:\+?91[\-\s]?)?([6-9]\d{9})", text, re.IGNORECASE)
    if m_phone:
        add("phone_number", m_phone.group(1), m_phone.group(0))

    # 7. Roll / Registration Number
    m_roll = re.search(r"(?:Registration\s*/\s*Roll\s+No|Roll\s+No|Registration\s+No|Reg\s+No|Hall\s+Ticket)\s*[:\-]?\s*([A-Za-z0-9\-_]{4,25})", text, re.IGNORECASE)
    if m_roll:
        add("roll_number", m_roll.group(1).strip(), m_roll.group(0))

    # 8. Institution Name
    m_inst = re.search(r"(?:Institution|College|University|Institute)\s*(?:Name)?\s*[:\-]?\s*([A-Za-z0-9\s,\.\-]{4,60})", text, re.IGNORECASE)
    if m_inst:
        val = m_inst.group(1).split("\n")[0].strip().strip(".,:-")
        if len(val) > 4 and val.lower() not in ["academic performance"]:
            add("institution_name", val, m_inst.group(0))

    # 9. 10th & 12th Percentages
    m_10 = re.search(r"(?:10th\s+Standard\s+Aggregate|10th\s+Aggregate|Secondary|SSLC|Matriculation)[^0-9\r\n]*(\d{1,2}(?:\.\d{1,2})?)\s*%", text, re.IGNORECASE)
    if m_10:
        add("tenth_percentage", m_10.group(1), m_10.group(0))

    m_12 = re.search(r"(?:12th\s*/\s*Pre-University\s+Aggregate|12th\s+Aggregate|Higher\s+Secondary|PUC|HSC|Pre-University)[^0-9\r\n]*(\d{1,2}(?:\.\d{1,2})?)\s*%", text, re.IGNORECASE)
    if m_12:
        add("twelfth_percentage", m_12.group(1), m_12.group(0))

    # 10. Annual Family Income
    m_inc = re.search(r"(?:Annual\s+Family\s+Income|Family\s+Income|Annual\s+Income|Gross\s+Income|Certified\s+Annual\s+Family\s+Income)[^0-9\r\n]*([0-9,]{4,12})", text, re.IGNORECASE)
    if m_inc:
        raw_num = m_inc.group(1).replace(",", "").strip()
        add("annual_family_income", raw_num, m_inc.group(0))

    # 11. Bank Details
    m_bank = re.search(r"(State\s+Bank\s+of\s+India|HDFC\s+Bank|ICICI\s+Bank|Punjab\s+National\s+Bank|Bank\s+of\s+Baroda|Canara\s+Bank|Union\s+Bank|Axis\s+Bank)", text, re.IGNORECASE)
    if m_bank:
        add("bank_name", m_bank.group(1).strip(), m_bank.group(0))

    m_acct = re.search(r"(?:Account\s+Number|A/C\s+No|Account\s+No)\s*[:\-]?\s*(\d{9,18})", text, re.IGNORECASE)
    if m_acct:
        add("bank_account_number", m_acct.group(1).strip(), m_acct.group(0), 0.99)

    m_ifsc = re.search(r"(?:IFSC\s+Code|IFSC)\s*[:\-]?\s*([A-Z]{4}0[A-Z0-9]{6})", text, re.IGNORECASE)
    if m_ifsc:
        add("ifsc_code", m_ifsc.group(1).strip(), m_ifsc.group(0), 0.99)

    # 12. Aadhaar Number
    m_aadh = re.search(r"(\d{4}\s*\d{4}\s*\d{4}|[X\d]{4}-[X\d]{4}-\d{4})", text)
    if m_aadh and ("aadhaar" in text.lower() or (doc_type and "aadhaar" in doc_type)):
        add("aadhaar_number", m_aadh.group(1).strip(), m_aadh.group(0), 0.99)

    return extracted

if __name__ == "__main__":
    import sys
    sys.path.insert(0, "backend")
    from app.services.document_engine import DocumentEngine

    for fname in ["aadhaar.pdf", "marksheet.pdf", "income_certificate.pdf", "bank_passbook.pdf"]:
        path = f"backend/sample_docs/{fname}"
        pdf_res = DocumentEngine.extract_text_from_pdf(path)
        res = extract_fields_from_raw_text(pdf_res["full_text"], fname)
        print(f"=== {fname} ({len(res)} fields) ===")
        for f in res:
            print(f"  {f['field']}: {f['value']} (from: '{f['evidence_text']}')")
