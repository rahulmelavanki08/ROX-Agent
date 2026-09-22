import re, sys
sys.path.insert(0, "backend")
from app.services.document_engine import DocumentEngine

def test():
    text = "Certified Annual Family Income: Rs. 2,40,000 /-"
    m = re.search(r"(?:Annual\s+Family\s+Income|Certified\s+Annual\s+Family\s+Income)[^0-9\r\n]*([0-9,]{4,12})", text, re.IGNORECASE)
    print("Match:", m.group(1) if m else None)

test()
