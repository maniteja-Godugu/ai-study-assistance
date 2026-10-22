from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    errors=exc.errors()
    error_details = []

    for error in errors:
        error_details.append({
        "field": error["loc"][-1],
        "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=422,
        content={"details":error_details}
        )