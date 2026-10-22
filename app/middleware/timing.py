from fastapi import Request
import time
import logging
logger=logging.getLogger(__name__)


async def timing_middleware(request:Request,call_next):
    start=time.perf_counter()
    logger.info("timing middle ware before callnext")

    response=await call_next(request)

    print("timing after ")

    duration = time.perf_counter() - start

    response.headers["X-Process-Time"] = str(duration)
    logger.info("timing middle ware after callnext")
    return response