from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any, Optional
from app.portal.mock_portal import mock_portal, FailureFlags

portal_router = APIRouter(prefix="/portal", tags=["Simulated Scholarship Portal"])

@portal_router.post("/api/session")
async def create_portal_session():
    session = mock_portal.create_session()
    return {"session_id": session.session_id, "status": "ACTIVE"}

@portal_router.get("/api/session/{session_id}")
async def get_portal_session_state(session_id: str):
    state = mock_portal.query_portal_state(session_id)
    return state

@portal_router.post("/api/step/{step_name}")
async def save_portal_step(session_id: str, step_name: str, payload: Dict[str, Any]):
    res = mock_portal.save_step(session_id, step_name, payload)
    status_code = res.get("status_code", 200)
    return JSONResponse(content=res, status_code=status_code)

@portal_router.post("/api/upload")
async def upload_portal_document(
    session_id: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...)
):
    contents = await file.read()
    file_size_kb = len(contents) / 1024.0
    dims = None

    if file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        from PIL import Image
        import io
        try:
            with Image.open(io.BytesIO(contents)) as img:
                dims = (img.width, img.height)
        except Exception:
            pass

    res = mock_portal.upload_document(
        session_id=session_id,
        doc_type=doc_type,
        filename=file.filename,
        file_size_kb=file_size_kb,
        mime_type=file.content_type or "application/octet-stream",
        dimensions=dims
    )
    return JSONResponse(content=res, status_code=res.get("status_code", 200))

@portal_router.post("/api/submit")
async def submit_portal_application(session_id: str = Form(...)):
    res = mock_portal.submit_application(session_id)
    return JSONResponse(content=res, status_code=res.get("status_code", 200))

@portal_router.get("/api/failure-injection")
async def get_failure_flags():
    return mock_portal.flags.model_dump()

@portal_router.post("/api/failure-injection")
async def update_failure_flags(flags: FailureFlags):
    mock_portal.flags = flags
    return {"message": "Failure flags updated", "current_flags": mock_portal.flags.model_dump()}

@portal_router.get("/view/{session_id}", response_class=HTMLResponse)
async def render_portal_view(session_id: str):
    state = mock_portal.query_portal_state(session_id)
    draft = state.get("draft_values", {})
    uploaded = state.get("uploaded_documents", [])
    submitted = state.get("submitted", False)
    ref = state.get("reference_number", "N/A")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>National Scholarship Portal 2026</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 text-slate-800 font-sans p-6">
        <div class="max-w-4xl mx-auto bg-white rounded-xl shadow border border-slate-200 p-8">
            <header class="border-b border-slate-200 pb-4 mb-6 flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-blue-900">National Merit & Need Scholarship Portal</h1>
                    <p class="text-sm text-slate-500">Government of Karnataka & Central Scholarship Board</p>
                </div>
                <div class="text-right">
                    <span class="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">Session: {session_id}</span>
                    <p class="text-xs text-slate-400 mt-1">Status: {'<span class="text-emerald-600 font-bold">SUBMITTED (' + ref + ')</span>' if submitted else '<span class="text-amber-600 font-bold">DRAFT IN PROGRESS</span>'}</p>
                </div>
            </header>

            <div class="grid grid-cols-2 gap-6 mb-6">
                <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <h2 class="font-semibold text-sm text-slate-700 uppercase tracking-wide mb-3">1. Personal Details</h2>
                    <p class="text-sm"><strong>Name:</strong> {draft.get('full_name', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>DOB:</strong> {draft.get('date_of_birth', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>Gender:</strong> {draft.get('gender', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>Category:</strong> {draft.get('category', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                </div>

                <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <h2 class="font-semibold text-sm text-slate-700 uppercase tracking-wide mb-3">2. Academic Details</h2>
                    <p class="text-sm"><strong>Institute:</strong> {draft.get('institution_name', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>Roll No:</strong> {draft.get('roll_number', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>10th %:</strong> {draft.get('tenth_percentage', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>12th %:</strong> {draft.get('twelfth_percentage', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-6 mb-6">
                <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <h2 class="font-semibold text-sm text-slate-700 uppercase tracking-wide mb-3">3. Financial & Bank Details</h2>
                    <p class="text-sm"><strong>Annual Family Income:</strong> {draft.get('annual_family_income', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>Bank:</strong> {draft.get('bank_name', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>Account:</strong> {draft.get('bank_account_number', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                    <p class="text-sm"><strong>IFSC:</strong> {draft.get('ifsc_code', '<span class="text-slate-400 italic">Not entered</span>')}</p>
                </div>

                <div class="bg-slate-50 p-4 rounded-lg border border-slate-200">
                    <h2 class="font-semibold text-sm text-slate-700 uppercase tracking-wide mb-3">4. Document Uploads</h2>
                    <ul class="text-sm space-y-1">
                        <li>Identity (Aadhaar): {'<span class="text-emerald-600 font-semibold">✓ Verified</span>' if 'doc_aadhaar' in uploaded else '<span class="text-amber-600">Pending</span>'}</li>
                        <li>Academic Marksheet: {'<span class="text-emerald-600 font-semibold">✓ Verified</span>' if 'doc_marksheet' in uploaded else '<span class="text-amber-600">Pending</span>'}</li>
                        <li>Income Certificate: {'<span class="text-emerald-600 font-semibold">✓ Verified</span>' if 'doc_income_cert' in uploaded else '<span class="text-amber-600">Pending</span>'}</li>
                        <li>Photograph: {'<span class="text-emerald-600 font-semibold">✓ Verified</span>' if 'doc_photo' in uploaded else '<span class="text-amber-600">Pending</span>'}</li>
                    </ul>
                </div>
            </div>

            <div class="border-t border-slate-200 pt-4 flex justify-between items-center text-xs text-slate-500">
                <p>Simulated Government Portal Architecture for ROX Verification</p>
                <p>Security: HTTPS / Zero-Trust Evidence Gate</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
