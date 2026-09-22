# ROX — Evidence-Gated Application Completion & Recovery Agent

> **Core Tagline:** *Fill it. Verify it. Recover it. Prove it.*  
> **Hackathon Track:** *A1. Evidence-Gated Self-Healing Agent Workflow*

ROX is a zero-trust autonomous application agent that uses user documents to complete complex, multi-step digital applications, verifies every critical action with machine-checkable deterministic evidence, detects inconsistent or failed states, safely recovers and re-plans, and **refuses to claim completion without verifiable evidence.**

---

## 🏛️ The Zero-Trust Separation Principle

```
               ┌────────────────────────────────────────┐
               │        LLM / Semantic Agent            │
               │  • Understands portal requirements     │
               │  • Extracts semantic field entities   │
               │  • Diagnoses failures & proposes fixes │
               └───────────────────┬────────────────────┘
                                   │ Action Proposal
                                   ▼
               ┌────────────────────────────────────────┐
               │           Execution Tools              │
               │  • Portal Adapter (DOM / API)          │
               │  • Document Adapter (PyMuPDF / Pillow) │
               │  • State Reconstructor                │
               └───────────────────┬────────────────────┘
                                   │ Raw Observations
                                   ▼
               ┌────────────────────────────────────────┐
               │     Deterministic Verifier Layer       │
               │  • On-disk file size & pixel dims      │
               │  • HTTP response status & checksums    │
               │  • Reference number regex & receipt    │
               └───────────────────┬────────────────────┘
                                   │ Machine-Checkable Evidence
                                   ▼
               ┌────────────────────────────────────────┐
               │            EVIDENCE GATE               │
               │   NO EVIDENCE  ==>  NO COMPLETION      │
               │   Only Gate declares VERIFIED_SUCCESS  │
               │   Cryptographic SHA-256 Proof Ledger   │
               └────────────────────────────────────────┘
```

> **The Golden Rule of ROX:**
> - The LLM may say: *"I propose this is fixed."*
> - The Verifier says: *"Here is the machine-checkable proof."*
> - **Only the Evidence Gate may declare: `VERIFIED_SUCCESS`.**

---

## ⚡ Key Features

1. **Google Gemini AI Cognitive Engine**:
   - Integrated with official `google-genai` SDK (`gemini-2.5-flash` / `gemini-2.0-flash`).
   - Dynamic API key configuration via `.env` or the dashboard UI modal.
   - Resilient intelligent fallback ensures 100% offline demonstration reliability.

2. **Cross-Document Consistency Guard (Conflict Gate)**:
   - Compares critical values across multiple documents.
   - *Example:* Aadhaar states DOB is `14/05/2007` while Marksheet states `15/05/2007`.
   - **ROX blocks automated continuation** and displays the Zero-Trust Conflict Resolution Modal.

3. **Bounded Self-Healing Engine (`MAX_RECOVERY_ATTEMPTS = 3`)**:
   - **Upload Error / Oversized Document**: Automatically compresses PDF stream below portal limits (e.g. 5.7MB → 72KB), verifies on-disk file, and re-uploads.
   - **Format / Dimension Error**: Automatically converts PNG → JPEG, resizes to strict `200x230` pixels, compresses to `<100KB`, verifies dimensions, and re-uploads.
   - **Session Expiration (401)**: Reconstructs state from last verified checkpoint and resumes seamlessly.
   - **Save Timeout (UNKNOWN State)**: Queries portal persistence layer to confirm whether state was actually saved before re-trying.
   - **Schema Mismatch**: Detects renamed DOM fields and remaps field schema.

4. **Irreversible Action Guard**:
   - Classifies actions by risk (LOW, MEDIUM, HIGH).
   - High-risk binding submissions unconditionally require:
     * 100% verified fields.
     * 0 unresolved conflicts.
     * All required documents verified.
     * Explicit human authorization.

5. **Cryptographic Proof Ledger**:
   - Append-only, SHA-256 hash-chained ledger (`previous_hash` → `entry_hash`).
   - Downloadable audit artifact (`rox-evidence-ledger.json`).

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.11+ (Python 3.13 tested)
- Node.js 18+ (Node v20 tested)

### 2. Start Backend Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Simulated Portal Live View: `http://localhost:8000/portal/view/demo`

### 3. Start Frontend Dashboard
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Running Automated Tests

Run the complete 15-test automated verification suite:

```bash
python -m pytest backend/tests -v
```

### Verified Test Cases:
- `test_critical_zero_trust_llm_hallucination_blocked`: Proves that LLM claiming success without verifier proof is **REJECTED** by the Evidence Gate.
- `test_dob_conflict_detection`: Cross-document conflict detection and blocking.
- `test_pdf_compression` & `test_image_adaptation_to_portal_contract`: Deterministic document adaptation.
- `test_mock_portal_upload_oversized_failure` & `test_mock_portal_upload_strict_photo_failure`: Real portal rejection hooks.
- `test_portal_session_expiration_hook` & `test_portal_save_timeout_unknown_state`: State reconstruction and timeout recovery.
- `test_bounded_recovery_exceeded`: Non-infinite loop guarantee.
- `test_full_rox_e2e_evidence_gated_workflow`: Complete 11-stage autonomous lifecycle from upload to `VERIFIED_SUCCESS`.

---

## 🏆 Complete Hackathon Demo Walkthrough (1-Click)

1. Open `http://localhost:5173`.
2. Click **⚡ Load Hackathon Demo Dataset (1-Click)** to load realistic sample government records:
   - `aadhaar.pdf` (DOB: 14/05/2007)
   - `marksheet.pdf` (DOB: 15/05/2007 — intentional conflict!)
   - `income_certificate.pdf` (5.7MB — triggers >2MB portal rejection!)
   - `photo.png` (1600x1200 PNG — triggers JPG 200x230 requirement!)
   - `bank_passbook.pdf` (Account & IFSC details)
3. Click **1. Analyze Application & Docs**:
   - The conflict detector flags the DOB discrepancy between Aadhaar and Marksheet.
   - The application is **BLOCKED**.
4. In the **Conflict Modal**, select the verified DOB (`14/05/2007`) and click **Resolve**.
5. In the **Plan Review Modal**, inspect the 15 verified steps and click **Approve & Authorize Plan**.
6. Click **3. Run Zero-Trust Execution**:
   - Watch the live Replay Timeline and the Simulated Portal DOM View update in real time.
   - **Self-Healing Event 1**: Income Certificate exceeds 2MB limit → Agent analyzes error → PyMuPDF compresses PDF → Re-upload verified.
   - **Self-Healing Event 2**: Photo format is PNG 1600x1200 → Agent analyzes error → Pillow converts to JPG, resizes to 200x230, compresses <100KB → Re-upload verified.
7. Click **4. Evidence-Backed Review**:
   - Inspect every single field citation with exact document provenance, page numbers, and confidence scores.
   - Check the **Irreversible Action Authorization** checkbox.
   - Click **Execute Verified Submission**.
8. **Evidence Gate Certification**:
   - System displays **VERIFIED SUCCESS** with verified Reference Number (`SCH-2026-XXXXX`) and cryptographic receipt hash.
9. Click **Cryptographic Proof Ledger** to inspect or download the JSON evidence ledger!
