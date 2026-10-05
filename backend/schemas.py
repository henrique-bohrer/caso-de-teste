from pydantic import BaseModel, EmailStr
from typing import Optional

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthSchema(BaseModel):
    credential_token: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
