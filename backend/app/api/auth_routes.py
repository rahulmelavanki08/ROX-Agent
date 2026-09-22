from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.auth_service import auth_service

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

class RequestOTPPayload(BaseModel):
    email: str

class VerifyOTPPayload(BaseModel):
    email: str
    otp: str

@auth_router.post("/request-otp")
async def request_otp(payload: RequestOTPPayload):
    """
    Generate and deliver a secure 6-digit OTP to the specified email address.
    """
    res = auth_service.request_otp(payload.email)
    if res.get("status") == "RATE_LIMITED":
        raise HTTPException(status_code=429, detail=res.get("message"))
    return res

@auth_router.post("/verify-otp")
async def verify_otp(payload: VerifyOTPPayload):
    """
    Verify the 6-digit OTP. On success, returns session token and authenticated user profile.
    """
    res = auth_service.verify_otp(payload.email, payload.otp)
    if res.get("status") != "SUCCESS":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@auth_router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get the currently authenticated user from the session token.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required")
    user = auth_service.get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return {
        "authenticated": True,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "authenticated_at": user.authenticated_at
        }
    }

@auth_router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Log out and invalidate the current session token.
    """
    if authorization:
        auth_service.logout(authorization)
    return {"status": "SUCCESS", "message": "Successfully logged out"}

@auth_router.get("/recent-deliveries")
async def get_recent_deliveries():
    """
    Returns recent OTP delivery events for evaluation, testing, and debugging.
    """
    return {
        "deliveries": auth_service.get_recent_deliveries()
    }
