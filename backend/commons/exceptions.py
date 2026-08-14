from fastapi import HTTPException


class WMSException(HTTPException):
    """Application-level HTTP exception for WMS business rules."""


def bad_request(message: str) -> WMSException:
    return WMSException(status_code=400, detail=message)


def conflict(message: str) -> WMSException:
    return WMSException(status_code=409, detail=message)
