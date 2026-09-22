import os
import io
import pymupdf as fitz
from PIL import Image, ImageDraw
from pathlib import Path

SAMPLE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def generate_aadhaar():
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    text = """GOVERNMENT OF INDIA / UNIQUE IDENTIFICATION AUTHORITY OF INDIA
AADHAAR IDENTIFICATION CARD

Name / Naam: Rahul Melavanki
Date of Birth / Janma Dina: 14/05/2007
Gender / Linga: Male / Purush
Social Category: General

Aadhaar Number: XXXX-XXXX-9481

Address:
#104, 3rd Cross, 5th Main,
Koramangala 4th Block, Bengaluru,
Karnataka, India - 560034

Verified Biometric ID: CERT-UID-2024-889104"""
    page.insert_text((50, 70), text, fontsize=12, lineheight=1.5)
    doc.save(str(SAMPLE_DIR / "aadhaar.pdf"))
    doc.close()
    print("Generated aadhaar.pdf")

def generate_marksheet():
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    text = """STATE BOARD OF SECONDARY & HIGHER SECONDARY EDUCATION
CUMULATIVE PERFORMANCE MARKSHEET

Candidate Name: Rahul Melavanki
Registration / Roll No: NITK2024CS089
Birth Date: 15/05/2007
Institution: National Institute of Technology

Academic Performance:
- 10th Standard Aggregate: 92.4% (Grade A+)
- 12th / Pre-University Aggregate: 89.6% (Grade A)
- Mathematics: 96 / 100
- Physics: 91 / 100
- Chemistry: 88 / 100
- Computer Science: 95 / 100

Result: FIRST CLASS WITH DISTINCTION
Verification Hash: CERT-ACAD-2024-4412"""
    page.insert_text((50, 70), text, fontsize=12, lineheight=1.5)
    doc.save(str(SAMPLE_DIR / "marksheet.pdf"))
    doc.close()
    print("Generated marksheet.pdf")

def generate_bank_passbook():
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    text = """STATE BANK OF INDIA - SAVINGS ACCOUNT PASSBOOK
Branch: Koramangala Branch (01423), Bengaluru

Account Holder: Rahul Melavanki
Account Number: 39485729104
Account Type: Regular Savings
Customer ID (CIF): 884910245
IFSC Code: SBIN0001423
MICR Code: 560002041

Current Balance: INR 48,250.00
Authorized Signatory Stamp: Verified Branch Seal"""
    page.insert_text((50, 70), text, fontsize=12, lineheight=1.5)
    doc.save(str(SAMPLE_DIR / "bank_passbook.pdf"))
    doc.close()
    print("Generated bank_passbook.pdf")

def generate_income_cert_oversized():
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    text = """REVENUE DEPARTMENT - TEHSILDAR OFFICE
INCOME AND CASTE CERTIFICATE

Certificate Number: REV-INC-2026-98102
Date of Issue: 12/01/2026

This is to certify that Sri Rahul Melavanki, son of Sri Anand Melavanki,
residing at #104, Koramangala 4th Block, Bengaluru, has an annual family income
from all legal sources as detailed below:

Certified Annual Family Income: Rs. 2,40,000 /-
(Rupees Two Lakh Forty Thousand Only)

Validity: 3 Years from issue date.
Digitally Signed by: Sub-Divisional Magistrate"""
    page.insert_text((50, 70), text, fontsize=12, lineheight=1.5)

    # Embed large uncompressed noise image buffer to make it ~3.2 MB
    img = Image.new("RGB", (1200, 1600), color=(240, 245, 250))
    draw = ImageDraw.Draw(img)
    for i in range(0, 1600, 10):
        draw.line([(0, i), (1200, i)], fill=(i % 255, (i * 3) % 255, (i * 7) % 255), width=4)
        draw.line([(i % 1200, 0), (i % 1200, 1600)], fill=((i * 5) % 255, i % 255, 120), width=4)
    
    bio = io.BytesIO()
    img.save(bio, format="BMP")  # Uncompressed BMP makes PDF > 2.5 MB!
    page.insert_image(fitz.Rect(50, 380, 545, 780), stream=bio.getvalue())

    doc.save(str(SAMPLE_DIR / "income_certificate.pdf"))
    doc.close()
    size_mb = os.path.getsize(str(SAMPLE_DIR / "income_certificate.pdf")) / (1024 * 1024)
    print(f"Generated income_certificate.pdf ({size_mb:.2f} MB)")

def generate_raw_photo():
    img = Image.new("RGBA", (1600, 1200), color=(220, 235, 245, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(600, 250), (1000, 650)], fill=(70, 130, 180, 255), outline=(30, 60, 100), width=8)
    draw.chord([(450, 680), (1150, 1380)], start=0, end=360, fill=(40, 90, 140, 255))
    
    img_path = str(SAMPLE_DIR / "photo.png")
    img.save(img_path, format="PNG")
    size_mb = os.path.getsize(img_path) / (1024 * 1024)
    print(f"Generated photo.png ({size_mb:.2f} MB, 1600x1200, PNG)")

if __name__ == "__main__":
    generate_aadhaar()
    generate_marksheet()
    generate_bank_passbook()
    generate_income_cert_oversized()
    generate_raw_photo()
