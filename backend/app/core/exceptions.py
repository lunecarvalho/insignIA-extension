from fastapi import Request
from fastapi.responses import JSONResponse


class InsignIAError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


async def http_exception_handler(request: Request, exc: InsignIAError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
