from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.infrastructure.db.base import get_db
from app.infrastructure.db.models.organization import Organization
from app.infrastructure.db.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    org_id: str
    role: str
    full_name: str

@router.post("/register", response_model=AuthTokenResponse)
def register_organization(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    org = Organization(name=req.org_name)
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role="owner"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role, org_id=org.id)
    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        org_id=org.id,
        role=user.role,
        full_name=user.full_name or ""
    )

@router.post("/login", response_model=AuthTokenResponse)
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=user.id, role=user.role, org_id=user.organization_id)
    return AuthTokenResponse(
        access_token=token,
        user_id=user.id,
        org_id=user.organization_id,
        role=user.role,
        full_name=user.full_name or ""
    )

@router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "organization_id": current_user.organization_id
    }
