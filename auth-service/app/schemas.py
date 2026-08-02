from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

type UserRole = Literal["client", "contractor"]


class AuthUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    full_name: str | None = None
    profile_picture: str | None = None
    email_verified: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    message: str
    user: AuthUserResponse


class RegisterRequest(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
    )
    email: EmailStr
    password: str = Field(
        min_length=6,
        max_length=72,
    )


class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    full_name: str


class TokenPayload(BaseModel):
    sub: str
    email: EmailStr
    role: UserRole
    full_name: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(
        min_length=6,
        max_length=72,
    )
