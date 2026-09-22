import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import api_router
from app.api.portal_routes import portal_router
from app.api.websocket import ws_router
from app.api.auth_routes import auth_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Evidence-Gated Application Completion & Recovery Agent. Fill it. Verify it. Recover it. Prove it.",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(api_router)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(portal_router)
app.include_router(ws_router)

# Mount storage directory for viewing adapted documents / proofs
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

@app.get("/")
async def root():
    return {
        "agent": settings.APP_NAME,
        "status": "ONLINE",
        "tagline": "Fill it. Verify it. Recover it. Prove it.",
        "api_docs": "/docs",
        "simulated_portal": "/portal/view/demo",
        "storage_path": str(settings.STORAGE_DIR)
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
