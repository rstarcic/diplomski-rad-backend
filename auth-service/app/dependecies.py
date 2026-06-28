from database import get_db
from errors import raise_auth_error
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.models import User
from app.utils.tokens import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    access_token = request.cookies.get("app_access")
    if not access_token:
        raise_auth_error("not_authenticated")

    payload = decode_access_token(access_token)
    user_id = payload.get("sub")
    if not user_id:
        raise_auth_error("invalid_or_expired_token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise_auth_error("user_not_found")

    return user
