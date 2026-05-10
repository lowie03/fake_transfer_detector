from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    business_name: str = ""
    phone: str = ""


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    business_name: str = ""
    phone: str = ""


class TokenResponse(BaseModel):
    token: str
    user: UserProfile


class SMSDetectRequest(BaseModel):
    text: str
    bank: str = ""
    amount: float = 0.0
    balance: float = 0.0
    date: str = ""
    time: str = ""
    account: str = ""


class DetectionResult(BaseModel):
    prediction: str
    confidence: float
    explanation: str
    action: str
    risk_level: str
    pipeline: str = ""
    timestamp: str = ""
    xai_insights: list[dict] = []


class LogEntry(BaseModel):
    timestamp: str
    input_type: str
    prediction: str
    confidence: str
    reason: str


class ReportStats(BaseModel):
    total_checks: int
    fake_count: int
    genuine_count: int
    inconclusive_count: int
    fake_pct: float
    genuine_pct: float


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    phone: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
