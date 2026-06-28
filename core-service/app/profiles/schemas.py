from datetime import datetime

from pydantic import BaseModel, EmailStr


class ProfileCreate(BaseModel):
    user_id: int
    email: EmailStr
    role: str
    full_name: str | None = None
    profile_picture: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    about: str | None = None
    profile_picture: str | None = None


class ProfileResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: str
    full_name: str | None = None
    profile_picture: str | None = None
    about: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    profile_completed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
