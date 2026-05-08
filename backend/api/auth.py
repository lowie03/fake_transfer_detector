from fastapi import APIRouter, HTTPException, Header
from backend.models.schemas import LoginRequest, SignupRequest, TokenResponse, UserProfile
from backend.core.auth_service import authenticate, register, create_token, get_user_by_token, update_user, _hash
from backend.models.schemas import UpdateProfileRequest

router = APIRouter()


def _to_profile(user: dict) -> UserProfile:
    return UserProfile(
        id=user["id"],
        name=user["name"],
        business_name=user["business_name"],
        email=user["email"],
        phone=user["phone"],
    )


def _require_token(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ", 1)[1]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    user = authenticate(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user["email"])
    return TokenResponse(token=token, user=_to_profile(user))


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = register(body.name, body.business_name, body.email, body.phone, body.password)
    if not user:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    token = create_token(user["email"])
    return TokenResponse(token=token, user=_to_profile(user))


@router.get("/me", response_model=UserProfile)
def me(authorization: str | None = Header(default=None)):
    user = _require_token(authorization)
    return _to_profile(user)


@router.patch("/profile", response_model=UserProfile)
def update_profile(body: UpdateProfileRequest, authorization: str | None = Header(default=None)):
    user = _require_token(authorization)
    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.business_name is not None:
        updates["business_name"] = body.business_name
    if body.phone is not None:
        updates["phone"] = body.phone
    if body.new_password:
        if not body.current_password:
            raise HTTPException(status_code=400, detail="Current password required")
        if user["password_hash"] != _hash(body.current_password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        updates["password_hash"] = _hash(body.new_password)
    updated = update_user(_get_token(authorization), updates)
    return _to_profile(updated)


def _get_token(authorization: str) -> str:
    return authorization.split(" ", 1)[1]
