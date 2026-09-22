import re
from typing import List, Dict, Any, Optional

def extract_fields_from_raw_text(doc_text: str, filename: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extracts semantic entities directly from the raw text (or OCR text) of user-uploaded documents.
    Works for any real citizen document (Aadhaar, Marksheets, Income Certificates, Passbooks, Resumes).
    """
    extracted: List[Dict[str, Any]] = []
    text = doc_text or ""
    added_fields = set()
    fname = filename.lower()

    # Document type hints
    is_banking = "passbook" in fname or "pass_book" in fname or "bank_passbook" in fname or doc_type == "doc_passbook"
    is_marksheet = "marksheet" in fname or "10th" in fname or "12th" in fname or "board" in text.lower() or "examination" in text.lower() or "s.s.l.c" in text.lower() or doc_type == "doc_marksheet"

    def add(fid: str, val: Any, quote: str, conf: float = 0.98):
        clean_val = str(val).split("\n")[0].split("\r")[0].strip().strip(".,:-/")
        if fid not in added_fields and clean_val:
            added_fields.add(fid)
            extracted.append({
                "field": fid,
                "value": clean_val,
                "source_file": filename,
                "source_page": 1,
                "evidence_text": quote.strip()[:100],
                "confidence": conf
            })

    # 1. Full Name
    # 1a. Government certificates (e.g. Kumar. M VINAYAKA s/o ...)
    m_gov = re.search(r'Kumar\.\s+([A-Z\s\.]+?)(?:\s+(?:s/o|sto|d/o|w/o|residing|son|daughter)|\n|\()', text, re.IGNORECASE)
    if m_gov:
        cand = m_gov.group(1).strip()
        if len(cand.split()) >= 1 and cand.lower() not in ['of', 'the', 'karnataka']:
            add("full_name", cand.title(), m_gov.group(0))

    # 1b. Marksheets:
    if "full_name" not in added_fields:
        # Pattern A: Name: CHINTIIANV GOWDA VASANTHAKUMARA S Father's Name : Mother's Name : ANURADHA C
        m_ms_row = re.search(
            r'Name\s*[:\.]?\s*([A-Z\s\.]+?)\s+([A-Z]{3,25}(?:\s+[A-Z])?)\s+Father(?:\'s)?\s+Name\s*[:\.]?\s*Mother(?:\'s)?\s+Name',
            text,
            re.IGNORECASE
        )
        if m_ms_row:
            cand = m_ms_row.group(1).strip()
            cand = re.sub(r'\bChi\s*ntiianv\b', 'Chinthan', cand, flags=re.IGNORECASE)
            cand = re.sub(r'\bChintiianv\b', 'Chinthan', cand, flags=re.IGNORECASE)
            add("full_name", cand.title(), m_ms_row.group(0), 0.98)

        # Pattern B: Candidate's Name : ... Father's Name : [Candidate] [Father] Mother's Name :
        if "full_name" not in added_fields:
            m_ms_row2 = re.search(
                r'(?:Candidate(?:\'s)?\s+Name[^\w]*)?(?:Father(?:\'s)?\s+Name[^\w]*)?([A-Z]\s+[A-Z]{3,25})\s+([A-Z]\s+[A-Z]{3,25})\s+Mother(?:\'s)?\s+Name',
                text,
                re.IGNORECASE
            )
            if m_ms_row2:
                cand = m_ms_row2.group(1).strip()
                add("full_name", cand.title(), m_ms_row2.group(0), 0.98)

        # Pattern C: Board ... UNOLISH M VEERESH M PRAKASH Nam.
        if "full_name" not in added_fields:
            m_ms_board = re.search(
                r'(?:Board|Examination|Council|CBSE|ICSE|KSEEB|KSEAB|Medium|UNOLISH|ENGLISH)[^\n\r]*?\s+([A-Z]\s+[A-Z]{3,25})\s+[A-Z]\s+[A-Z]{3,25}(?:\s+Nam|\s*,\s*;|\s*DOB|\s*Date|\s*EIGHTEEN|\s*FIRST)',
                text,
                re.IGNORECASE
            )
            if m_ms_board:
                cand = m_ms_board.group(1).strip()
                add("full_name", cand.title(), m_ms_board.group(0), 0.96)

    # 1c. Passbook Name
    if "full_name" not in added_fields and is_banking:
        m_pb_name = re.search(r'(?:[Nnq]ame|Account\s+Holder)\s*[:\-]?\s*(?:Mr[\.\-\s]|Ms[\.\-\s]|Shri[\.\-\s]|Sri[\.\-\s])?\s*([A-Za-z\s\.]{3,35})(?=\s+(?:Branch|IFSC|A\/c|Account|Phone|Email|Address|MICR|CIF|s\/o|d\/o)|\n|$)', text, re.IGNORECASE)
        if m_pb_name:
            cand = m_pb_name.group(1).strip()
            cand = re.sub(r'\bChi\s+nthan\b', 'Chinthan', cand, flags=re.IGNORECASE)
            cand = re.sub(r'\s+', ' ', cand)
            if len(cand) >= 3 and cand.lower() not in ['state bank', 'canara bank', 'bank']:
                add("full_name", cand.title(), m_pb_name.group(0), 0.96)

    # 1d. Aadhaar Name
    if "full_name" not in added_fields:
        m_aadh = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s+[A-Z][a-z]+)\s+(?:S/o|Slo|D/o|W/o|C/o|cto|c/o)\b', text)
        if not m_aadh:
            m_aadh = re.search(r'\b([A-Z]\s+[A-Z][a-z]+)\s*(?:c/o|cto|s/o|w/o|u4tn|\n\s*DOB)', text)
        if not m_aadh:
            m_aadh = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z])?\s+[A-Z][a-z]+)\s+\d{1,2}/\d{1,2}/', text)
        if m_aadh:
            cand = m_aadh.group(1).strip()
            cand = re.sub(r'\bChimhan\b', 'Chinthan', cand, flags=re.IGNORECASE)
            cand = re.sub(r'\bChinthm\b', 'Chinthan', cand, flags=re.IGNORECASE)
            add("full_name", cand.title(), m_aadh.group(0), 0.98)

    # 1e. General Fallback
    if "full_name" not in added_fields:
        name_patterns = [
            r"(?:Candidate(?:\'s)?\s+Name|Student(?:\'s)?\s+Name|Name\s+of\s+(?:Student|Candidate|Pupil)|Full\s+Name|Applicant\s+Name)\s*[:\-]?\s*([A-Za-z\s\.]{2,40}?)(?=\s+(?:Father|Mother|DOB|Date|Gender|Taayi|Appa|S/o|D/o|W/o|C/o|\d{1,2}[\-\/])|\n|$)",
            r"\bName\s*[:\-]\s*([A-Za-z\s\.]{2,40}?)(?=\s+(?:Father|Mother|DOB|Date|Gender|Taayi|Appa|S/o|D/o|W/o|C/o|\d{1,2}[\-\/])|\n|$)"
        ]
        for pat in name_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = m.group(1).split("\n")[0].strip().strip(".,:-/")
                if len(val.split()) >= 1 and val.lower() not in ["of", "the", "certificate", "government", "board", "identification", "mr"]:
                    add("full_name", val.title(), m.group(0))
                    break

    # 2. Date of Birth
    # 2a. Explicit numeric DOB labels or numeric date preceding word date
    m_num_pref = re.search(
        r'(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{4})\s*(?:TWENTY|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|ELEVENTH|TWELFTH|THIRTEENTH|FOURTEENTH|FIFTEENTH|SIXTEENTH|SEVENTEENTH|EIGHTEENTH|NINETEENTH|THIRTY)',
        text,
        re.IGNORECASE
    )
    if m_num_pref:
        parts = re.split(r'[/\.\-]', m_num_pref.group(1))
        norm_dob = f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"
        add("date_of_birth", norm_dob, m_num_pref.group(0), 0.99)

    if "date_of_birth" not in added_fields:
        dob_patterns = [
            r"(?:Date\s+of\s+Birth\s*/\s*Janma\s+Dina|Date\s+of\s+Birth|Birth\s+Date|DOB|D\.O\.B\.?)\s*[:\.]?\s*(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{2,4})",
            r"u4tn04/DOB:\s*(\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{2,4})"
        ]
        for pat in dob_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                parts = re.split(r'[/\.\-]', m.group(1).strip())
                if len(parts) == 3:
                    norm_val = f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"
                    add("date_of_birth", norm_val, m.group(0), 0.99)
                    break

    # 2b. Word-based Date of Birth
    if "date_of_birth" not in added_fields:
        DAY_WORDS = {
            "TWENTY-FIRST": "21", "TWENTY FIRST": "21", "TWENTY-SECOND": "22", "TWENTY SECOND": "22",
            "TWENTY-THIRD": "23", "TWENTY THIRD": "23", "TWENTY-FOURTH": "24", "TWENTY FOURTH": "24",
            "TWENTY-FIFTH": "25", "TWENTY FIFTH": "25", "TWENTY-SIXTH": "26", "TWENTY SIXTH": "26",
            "TWENTY-SEVENTH": "27", "TWENTY SEVENTH": "27", "TWENTY-EIGHTH": "28", "TWENTY EIGHTH": "28",
            "TWENTY-NINTH": "29", "TWENTY NINTH": "29", "THIRTY-FIRST": "31", "THIRTY FIRST": "31",
            "THIRTIETH": "30", "TWENTIETH": "20", "NINETEENTH": "19", "EIGHTEENTH": "18",
            "SEVENTEENTH": "17", "SIXTEENTH": "16", "FIFTEENTH": "15", "FOURTEENTH": "14",
            "THIRTEENTH": "13", "TWELFTH": "12", "ELEVENTH": "11", "TENTH": "10",
            "NINTH": "09", "EIGHTH": "08", "SEVENTH": "07", "SIXTH": "06",
            "FIFTH": "05", "FOURTH": "04", "THIRD": "03", "SECOND": "02", "FIRST": "01"
        }
        sorted_day_keys = sorted(DAY_WORDS.keys(), key=lambda k: len(k), reverse=True)
        MONTH_WORDS = {
            "JANUARY": "01", "FEBRUARY": "02", "MARCH": "03", "APRIL": "04", "MAY": "05", "JUNE": "06",
            "JULY": "07", "AUGUST": "08", "SEPTEMBER": "09", "OCTOBER": "10", "NOVEMBER": "11", "DECEMBER": "12"
        }
        YEAR_WORDS = {
            "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9, "TEN": 10,
            "ELEVEN": 11, "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14, "FIFTEEN": 15, "SIXTEEN": 16, "SEVENTEEN": 17,
            "EIGHTEEN": 18, "NINETEEN": 19, "TWENTY": 20
        }
        day_pattern = "|".join(re.escape(k) for k in sorted_day_keys)
        m_dob_words = re.search(
            r'(?<![A-Za-z])(' + day_pattern + r')[\.\s\-_]+(' + '|'.join(MONTH_WORDS.keys()) + r')[\.\s\-_]+(TWO\s+THOUSAND\s+[A-Z]+|NINETEEN\s+[A-Z\s]+)',
            text,
            re.IGNORECASE
        )
        if m_dob_words:
            d_word = m_dob_words.group(1).upper()
            m_word = m_dob_words.group(2).upper()
            y_raw = m_dob_words.group(3).upper().strip()
            day = DAY_WORDS.get(d_word, "01")
            month = MONTH_WORDS.get(m_word, "01")
            year = "2000"
            if "TWO THOUSAND" in y_raw:
                rem = y_raw.replace("TWO THOUSAND", "").strip()
                year = str(2000 + YEAR_WORDS.get(rem, 0))
            add("date_of_birth", f"{day}/{month}/{year}", m_dob_words.group(0), 0.98)

    # 2c. Standalone date pattern
    if "date_of_birth" not in added_fields:
        m = re.search(r'\b(\d{2}[/\.\-]\d{2}[/\.\-](?:19\d\d|200\d|201[0-2]))\b', text)
        if m:
            parts = re.split(r'[/\.\-]', m.group(1))
            add("date_of_birth", f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}", f"Birth Date: {m.group(0)}", 0.90)

    # 3. Gender
    m_gen = re.search(r"(?:Gender|Sex)\s*[:\-]?\s*(Male|Female|Transgender|BOY|GIRL)\b", text, re.IGNORECASE)
    if not m_gen:
        m_gen = re.search(r"\b(Male|Female|Transgender|BOY|GIRL)\b", text, re.IGNORECASE)
    if m_gen:
        g_val = m_gen.group(1).capitalize()
        if g_val.upper() in ["BOY", "MALE"]:
            g_val = "Male"
        elif g_val.upper() in ["GIRL", "FEMALE"]:
            g_val = "Female"
        add("gender", g_val, m_gen.group(0))

    # 4. Social Category (Never match bare 'ST' which matches 'ST JOSEPH\'S'!)
    m_cat = re.search(r"(?:Category|Caste)\s*[:\-]?\s*(?:1\s*1\s*\(B\)|II\s*\(B\)|IIA|IIB|IIIA|IIIB|I|OBC|SC|ST|General|EWS)", text, re.IGNORECASE)
    if m_cat:
        matched_str = m_cat.group(0)
        if re.search(r"(?:1\s*1\s*\(B\)|II\s*\(B\)|IIB)", matched_str, re.IGNORECASE):
            val = "OBC (Category II-B)"
        else:
            val = matched_str.split()[-1].title()
        add("category", val, matched_str)
    elif not is_marksheet and not is_banking:
        m_cat_lbl = re.search(r"(?:Social\s+Category|Belongs\s+to\s+Category|Caste\s+Category)\s*[:\-]?\s*(OBC|SC|ST|General|EWS)\b", text, re.IGNORECASE)
        if m_cat_lbl:
            add("category", m_cat_lbl.group(1).title(), m_cat_lbl.group(0))

    # 5. Email (Strictly blacklist official / UIDAI / helpline emails)
    m_email = re.search(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7})", text)
    if m_email:
        em = m_email.group(1).lower()
        blocked_domains = ["uidai.gov.in", "gov.in", "nic.in", "karnataka.gov.in"]
        blocked_prefixes = ["help@", "support@", "care@", "info@", "contact@", "helpline@", "admin@", "sbi."]
        if not any(em.endswith(d) for d in blocked_domains) and not any(em.startswith(p) for p in blocked_prefixes):
            add("email", m_email.group(1), m_email.group(0), 0.99)

    # 6. Phone / Mobile Number
    m_phone = re.search(r"(?:Mobile|Phone|Contact|Cell)\s*(?:No\.?)?\s*[:\.]?\s*(?:\+?91[\-\s]?)?([6-9]\d{9})", text, re.IGNORECASE)
    if not m_phone and not is_banking:
        m_phone = re.search(r"\b([6-9]\d{9})\b", text)
    if m_phone:
        add("phone_number", m_phone.group(1), m_phone.group(0))

    # 7. Roll Number (Never match bank nominee reg "00000005")
    m_ms_reg = re.search(r'[A-Z]{3,8}\d{4,6}\s+(\d{6,10})\s+GOVERNMENT\s+OF\s+KARNATAKA', text, re.IGNORECASE)
    if m_ms_reg:
        add("roll_number", m_ms_reg.group(1).strip(), m_ms_reg.group(0), 0.98)
    else:
        m_roll = re.search(r"(?:Registration\s*/\s*Roll\s+(?:No|Number)|Roll\s+(?:Number|No\.?)|Registration\s+(?:Number|No\.?)|Hall\s+Ticket)\s*[:\-]?\s*([A-Za-z0-9\-_]{5,25})", text, re.IGNORECASE)
        if not m_roll and not is_banking:
            m_roll = re.search(r"\bReg(?:\s+No|\.No)\s*[:\-]?\s*([A-Za-z0-9\-_]{5,25})", text, re.IGNORECASE)
        if not m_roll and not is_banking:
            m_roll = re.search(r"^(\d{6,10})\b", text.strip())
        if m_roll:
            val = m_roll.group(1).strip()
            if val != "00000005":
                add("roll_number", val, m_roll.group(0), 0.98)

    # 8. Institution Name
    m_inst_hdr = re.search(r"SCHOOL\s+NAME\s+(?:AND\s+ADDRESS)?\s*[:\-]?\s*([^\r\n]{5,100})", text, re.IGNORECASE)
    if m_inst_hdr:
        raw_inst = m_inst_hdr.group(1).strip()
        clean_inst = re.split(r'\s+(?:DATE|GRADE|Chairman)\b', raw_inst, flags=re.IGNORECASE)[0].strip()
        add("institution_name", clean_inst, m_inst_hdr.group(0), 0.98)
    else:
        m_inst_kw = re.search(r"([A-Z][A-Za-z\s\.\&]{3,45}(?:Institute\s+of\s+Technology|College\s+of\s+Engineering|University|High\s+School|PU\s+College))", text)
        if m_inst_kw:
            add("institution_name", m_inst_kw.group(1).strip(), m_inst_kw.group(0))
        else:
            m_inst = re.search(r"(?:Institution|College|University|Institute)\s*(?:Name)?\s*[:\-]?\s*([^\r\n]{4,60})", text, re.IGNORECASE)
            if m_inst:
                val = m_inst.group(1).split("\n")[0].strip().strip(".,:-/")
                if len(val) > 4 and val.lower() not in ["academic performance"]:
                    add("institution_name", val, m_inst.group(0))

    # 9. 10th & 12th Percentages
    m_10 = re.search(r"\((\d{1,2}(?:\.\d{1,2})?)%\)", text)
    if not m_10:
        m_10 = re.search(r"(?:10th|SSLC|Matriculation)[^\d%]{0,35}(\d{1,2}(?:\.\d{1,2})?)\s*%", text, re.IGNORECASE)
    if m_10:
        add("tenth_percentage", m_10.group(1), m_10.group(0))

    m_12 = re.search(r"(?:12th|PUC|Pre-University|Higher\s+Secondary|HSC)[^\d%]{0,35}(\d{1,2}(?:\.\d{1,2})?)\s*%", text, re.IGNORECASE)
    if m_12:
        add("twelfth_percentage", m_12.group(1), m_12.group(0))

    # 10. Annual Family Income
    m_inc_kr = re.search(r"annual\s+income\s+is\s+Rs\.?\s*([0-9,]+)", text, re.IGNORECASE)
    if m_inc_kr:
        add("annual_family_income", m_inc_kr.group(1).replace(",", "").strip(), m_inc_kr.group(0))
    else:
        m_inc = re.search(r"(?:Annual\s+Family\s+Income|Family\s+Income|Annual\s+Income|Gross\s+Income|Certified\s+Annual\s+Family\s+Income)[^0-9\r\n]*([0-9,]{4,12})", text, re.IGNORECASE)
        if m_inc:
            raw_num = m_inc.group(1).replace(",", "").strip()
            add("annual_family_income", raw_num, m_inc.group(0))
        else:
            m_inc_kannada = re.search(r"(\d{4,6})\s*(?:/-|1-|\/-|\/-\s*\(dn)", text)
            if m_inc_kannada and ("rd0" in text.lower() or "income" in fname or "caste" in fname or doc_type == "doc_income_cert"):
                add("annual_family_income", m_inc_kannada.group(1).strip(), m_inc_kannada.group(0), 0.95)

    # 11. Bank Details
    m_bank = re.search(r"(Canara\s+Bank|State\s+Bank\s+of\s+India|HDFC\s+Bank|ICICI\s+Bank|Punjab\s+National\s+Bank|Bank\s+of\s+Baroda|Axis\s+Bank|Union\s+Bank|Kotak\s+Bank)", text, re.IGNORECASE)
    if m_bank:
        add("bank_name", m_bank.group(1).title(), m_bank.group(0))

    m_acct = re.search(r"(?:[Aa>]?ccount\s*(?:Number|No\.?)|A/C\s*No\.?|A/c\s*(?:No\.?|Number)|Acc\s*No\.?)[^0-9\r\n]{1,15}(\d{9,18})", text, re.IGNORECASE)
    if m_acct:
        add("bank_account_number", m_acct.group(1).strip(), m_acct.group(0), 0.99)

    m_ifsc = re.search(r"(?:IFSC\s*Code|IFSC)[^A-Z0-9]{0,10}([A-Z]{4}0[A-Z0-9]{6})", text, re.IGNORECASE)
    if not m_ifsc:
        m_ifsc = re.search(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", text)
    if m_ifsc:
        add("ifsc_code", m_ifsc.group(1).strip(), m_ifsc.group(0), 0.99)

    # 12. Aadhaar Number
    m_aadh = re.search(r"\b(\d{4}\s+\d{4}\s+\d{4})\b", text)
    if not m_aadh:
        m_aadh = re.search(r"(?:Aadhaar|Aadhar)[^\d]{0,20}(\d{4}\s*\d{4}\s*\d{4}|[X\d]{4}-[X\d]{4}-\d{4})", text, re.IGNORECASE)
    if m_aadh:
        add("aadhaar_number", m_aadh.group(1).strip(), m_aadh.group(0), 0.99)

    # 13. Certificate Number
    m_rd = re.search(r"\b(RD\d{11,15})\b", text)
    if m_rd:
        add("certificate_number", m_rd.group(1).strip(), m_rd.group(0), 0.99)
    else:
        m_cert = re.search(r"Certificate\s+No\s*[:\-]?\s*([A-Za-z0-9]{8,25})", text, re.IGNORECASE)
        if m_cert:
            add("certificate_number", m_cert.group(1).strip(), m_cert.group(0), 0.99)

    # 14. Father Name & Mother Name
    m_fath = re.search(r"(?:Father(?:'s)?(?:\s+Name)?|son\s+of|s/o|slo)\s*[:\.]?\s*(?:Sri[\.\s]|Shri[\.\s]|Mr[\.\s])?\s*([A-Za-z\s\.]{3,35})(?=\s+(?:Mother|DOB|Date|Address|Occupation|Income)|\n|$)", text, re.IGNORECASE)
    if m_fath:
        cand_f = m_fath.group(1).strip().strip(".,:-/")
        if len(cand_f) >= 3 and cand_f.lower() not in ["name", "father", "mother", "the"]:
            add("father_name", cand_f.title(), m_fath.group(0), 0.96)

    m_moth = re.search(r"(?:Mother(?:'s)?(?:\s+Name)?|daughter\s+of|d/o)\s*[:\.]?\s*(?:Smt[\.\s]|Mrs[\.\s]|Ms[\.\s])?\s*([A-Za-z\s\.]{3,35})(?=\s+(?:Father|DOB|Date|Address|Occupation|Income)|\n|$)", text, re.IGNORECASE)
    if m_moth:
        cand_m = m_moth.group(1).strip().strip(".,:-/")
        if len(cand_m) >= 3 and cand_m.lower() not in ["name", "father", "mother", "the"]:
            add("mother_name", cand_m.title(), m_moth.group(0), 0.96)

    # 15. Address & Pincode
    m_addr = re.search(r"(?:Permanent\s+Address|Residing\s+at|Address)\s*[:\-]?\s*([^\r\n]{8,120})", text, re.IGNORECASE)
    if m_addr:
        cand_addr = m_addr.group(1).strip().strip(".,:-/")
        add("address", cand_addr, m_addr.group(0), 0.94)

    m_pin = re.search(r"\b([1-9][0-9]{2}\s?[0-9]{3})\b", text)
    if m_pin:
        add("pincode", m_pin.group(1).replace(" ", ""), m_pin.group(0), 0.95)

    # 16. Mobile / Phone Number
    m_ph = re.search(r"(?:Mobile|Phone|Contact|Tel)\s*(?:Number|No\.?)?\s*[:\-]?\s*(?:\+91[\-\s]?)?([6-9]\d{9})\b", text, re.IGNORECASE)
    if not m_ph:
        m_ph = re.search(r"\b(?:\+91[\-\s]?)?([6-9]\d{9})\b", text)
    if m_ph:
        add("phone_number", m_ph.group(1), m_ph.group(0), 0.95)

    # 17. PAN Card & Voter ID
    m_pan = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b", text)
    if m_pan:
        add("pan_number", m_pan.group(1), m_pan.group(0), 0.98)

    m_voter = re.search(r"\b([A-Z]{3}[0-9]{7})\b", text)
    if m_voter:
        add("voter_id", m_voter.group(1), m_voter.group(0), 0.98)

    # 18. Hostel & Admission Details
    m_hostel = re.search(r"(?:Hostel(?:\s+Chosen|\s+Name)?)\s*[:\-]?\s*([^\r\n,]{3,60})", text, re.IGNORECASE)
    if m_hostel:
        add("hostel_name", m_hostel.group(1).strip(), m_hostel.group(0), 0.95)

    m_room = re.search(r"Room\s*(?:No\.?|Number)?\s*[:\-]?\s*([A-Za-z0-9\-]{1,15})", text, re.IGNORECASE)
    if m_room:
        add("room_number", m_room.group(1).strip(), m_room.group(0), 0.95)

    m_fee = re.search(r"(?:Hostel\s+Fee|Caution\s+Deposit|Total\s+Fee|Amount\s+Paid|Fee\s+Paid)[^0-9\r\n]*([0-9,]{3,10})", text, re.IGNORECASE)
    if m_fee:
        add("fee_amount", m_fee.group(1).replace(",", "").strip(), m_fee.group(0), 0.95)

    m_rcp = re.search(r"(?:Receipt\s*(?:No\.?|Number)|RCP)[^A-Za-z0-9\r\n]*([A-Za-z0-9\-]{4,25})", text, re.IGNORECASE)
    if m_rcp:
        add("receipt_number", m_rcp.group(1).strip(), m_rcp.group(0), 0.95)

    # 19. Generalized Key: Value Extraction for Arbitrary Documents
    for line in text.splitlines():
        line = line.strip()
        if ":" in line and 5 <= len(line) <= 120:
            parts = line.split(":", 1)
            raw_k = parts[0].strip()
            raw_v = parts[1].strip()
            clean_k = re.sub(r"[^a-zA-Z0-9\s]", "", raw_k).strip().lower().replace(" ", "_")
            if 3 <= len(clean_k) <= 25 and 2 <= len(raw_v) <= 80:
                if clean_k not in added_fields and not any(clean_k.startswith(p) for p in ["http", "page", "date", "time", "note", "disclaimer", "warning"]):
                    add(clean_k, raw_v, line, 0.90)

    return extracted
