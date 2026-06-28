from fastapi import HTTPException


def raise_not_found(detail: str = "Not found"):
    raise HTTPException(status_code=404, detail=detail)


def raise_bad_request(detail: str = "Bad request"):
    raise HTTPException(status_code=400, detail=detail)
