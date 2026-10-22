from fastapi import FastAPI
from app.exceptions.handlers import validation_exception_handler
from fastapi.exceptions import RequestValidationError
from app.routes import chat
from app.routes import auth
from app.routes import history
from app.database.base import Base
from app.models.users import User
from app.models.studysession import StudySession
from app.database.connection import engine
from app.middleware.timing import timing_middleware
from app.middleware.rate_limit import rate_limit_middleware
from app.security.rate_limit_slowapi import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(title="AI Study Assistant")
app.state.limiter=limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


app.middleware("http")(timing_middleware)
app.middleware("http")(rate_limit_middleware)



Base.metadata.create_all(bind=engine)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)
app.include_router(chat.router)
app.include_router(auth.router)
app.include_router(history.router)