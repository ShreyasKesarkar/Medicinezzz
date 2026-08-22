from typing import Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse

def success_response(data: Any = None, message: str = "Success") -> dict:
    return {
        "data": data,
        "message": message
    }

class APIException(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
