from datetime import datetime
from typing import Any, Literal

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from app.reviews.schemas import TargetReviewsResponse


# =========================================================
# PROFILE REQUEST SCHEMAS
# =========================================================


class ProfileCreate(BaseModel):
    user_id: int
    email: EmailStr
    role: Literal["client", "contractor"]
    full_name: str | None = None
    profile_picture: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    about: str | None = None
    profile_picture: str | None = None


class SkillUpdate(BaseModel):
    name: str


class PortfolioItemUpdate(BaseModel):
    title: str
    description: str | None = None
    image_url: str | None = None
    project_url: str | None = None


class ProfilePageUpdate(BaseModel):
    profile: ProfileUpdate
    skills: list[SkillUpdate] | None = None
    portfolio: list[PortfolioItemUpdate] | None = None

    @model_validator(mode="before")
    @classmethod
    def accept_flat_profile_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict) or "profile" in data:
            return data

        profile_fields = set(ProfileUpdate.model_fields)

        profile_data = {
            field: value
            for field, value in data.items()
            if field in profile_fields
        }

        if not profile_data:
            return data

        return {
            "profile": profile_data,
            "skills": data.get("skills"),
            "portfolio": data.get("portfolio"),
        }


# =========================================================
# INTERNAL SERVICE SCHEMAS
# =========================================================


class InternalContractorProfileResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: Literal["contractor"]
    full_name: str | None = None
    about: str | None = None
    phone: str | None = None
    city: str | None = None
    country: str | None = None

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# COMMON PROFILE RESPONSE SCHEMAS
# =========================================================


class ProfileResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: str
    full_name: str | None = None
    profile_picture: str | None = Field(
        default=None,
        validation_alias=AliasPath("display_profile_picture"),
    )
    about: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    profile_completed: bool
    has_uploaded_picture: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class PortfolioItemResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    image_url: str | None = None
    project_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# PRIVATE PROFILE PAGE RESPONSES
# =========================================================


class BaseProfilePageResponse(BaseModel):
    profile: ProfileResponse
    reviews: TargetReviewsResponse


class ClientProfilePageResponse(BaseProfilePageResponse):
    page_type: Literal["client"] = "client"


class ContractorProfilePageResponse(BaseProfilePageResponse):
    page_type: Literal["contractor"] = "contractor"
    skills: list[SkillResponse]
    portfolio: list[PortfolioItemResponse]


ProfilePageResponse = (
    ClientProfilePageResponse
    | ContractorProfilePageResponse
)


# =========================================================
# PUBLIC PROFILE SCHEMAS
# =========================================================


class PublicProfile(BaseModel):
    user_id: int
    full_name: str | None = None
    profile_picture: str | None = None
    email: EmailStr
    phone: str | None = None
    city: str | None = None
    country: str | None = None
    created_at: datetime
    about: str | None = None


class ContractorPublicProfile(PublicProfile):
    pass


class ClientPublicProfile(PublicProfile):
    pass


class ContractorPublicPortfolioItem(BaseModel):
    id: int
    title: str
    description: str | None = None
    project_url: str | None = None
    image_url: str | None = None


class ContractorPublicSkill(BaseModel):
    id: int
    name: str


class ContractorPublicStat(BaseModel):
    id: str
    value: int | float | str
    subtitle: str


class ClientPublicStat(BaseModel):
    id: str
    value: int | float | str
    subtitle: str


class ContractorPublicProfileResponse(BaseModel):
    profile: ContractorPublicProfile
    portfolio: list[ContractorPublicPortfolioItem]
    skills: list[ContractorPublicSkill]
    stats: list[ContractorPublicStat]
    reviews: TargetReviewsResponse


class ClientPublicProfileResponse(BaseModel):
    profile: ClientPublicProfile
    stats: list[ClientPublicStat]
    reviews: TargetReviewsResponse
