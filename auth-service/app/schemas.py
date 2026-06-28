from pydantic import BaseModel, EmailStr, Field


class AuthUserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    full_name: str | None = None
    profile_picture: str | None = None
    email_verified: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str
    user: AuthUserResponse


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class RegisterResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    full_name: str

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    sub: str
    email: EmailStr
    role: str
    full_name: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=72)
