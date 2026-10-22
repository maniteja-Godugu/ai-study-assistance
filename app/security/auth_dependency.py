
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.session import SessionLocal
from app.models.users import User
from app.security.jwt import SECRET_KEY, ALGORITHM
import logging
logger=logging.getLogger(__name__)


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials =Depends(bearer_scheme)
     
):
    db=SessionLocal()
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials please login again",
        headers={"WWW-Authenticate": "Bearer"}
    )

    # Step 1: Decode and verify JWT
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Step 2: Extract subject
        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject:
            raise credentials_exception

        user_id = int(subject)

    except (jwt.InvalidTokenError, ValueError, TypeError):
        logger.exception(f"acesstoken error during user authorization: {exc}")
        raise credentials_exception

    # Step 3: Retrieve user from database
    try:
        user = db.scalar(
            select(User).where(User.id == user_id)
        )
    
    except SQLAlchemyError as exc:
        
        logger.exception(f" database failure during user authorization: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable"
        ) from exc

    # Step 4: Check user existence
    if user is None:
        raise credentials_exception

    # Step 5: Return authenticated user
    logger.info("user aithorized sucessfully")
    return user