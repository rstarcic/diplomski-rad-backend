import json

from app.profiles.schemas import ProfilePageUpdate, ProfileUpdate
from errors import raise_core_error
from fastapi import Request
from starlette.datastructures import UploadFile

PROFILE_PICTURE_FIELD = "profile_picture"


def _json_form_field(value: object) -> object:
    if value is None or value == "":
        return None

    if not isinstance(value, str):
        raise_core_error("invalid_multipart_json")

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        raise_core_error("invalid_multipart_json")


def _profile_payload_from_form(form) -> dict:
    payload = {}

    for field in ProfileUpdate.model_fields:
        value = form.get(field)
        if isinstance(value, str):
            payload[field] = value

    return payload


async def _read_profile_picture_blob(file: UploadFile) -> tuple[bytes, str]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise_core_error("profile_picture_invalid_type")

    content = await file.read()
    if not content:
        raise_core_error("profile_picture_empty")

    return content, file.content_type


async def _profile_picture_from_form(
    form,
) -> tuple[bytes | None, str | None, str | None]:
    value = form.get(PROFILE_PICTURE_FIELD)

    if isinstance(value, UploadFile):
        blob, content_type = await _read_profile_picture_blob(value)
        return blob, content_type, None

    if isinstance(value, str) and value:
        return None, None, value

    return None, None, None


async def _profile_update_from_multipart(
    request: Request,
) -> tuple[ProfilePageUpdate, bytes | None, str | None]:
    form = await request.form()

    payload = _profile_payload_from_form(form)
    profile_picture_blob, profile_picture_content_type, profile_picture_url = (
        await _profile_picture_from_form(form)
    )

    if profile_picture_url:
        payload["profile_picture"] = profile_picture_url

    data = ProfilePageUpdate(
        profile=ProfileUpdate(**payload),
        skills=_json_form_field(form.get("skills")),
        portfolio=_json_form_field(form.get("portfolio")),
    )

    return data, profile_picture_blob, profile_picture_content_type


async def profile_update_from_request(
    request: Request,
) -> tuple[ProfilePageUpdate, bytes | None, str | None]:
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("multipart/form-data"):
        return await _profile_update_from_multipart(request)

    return ProfilePageUpdate.model_validate(await request.json()), None, None
