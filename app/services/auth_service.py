from app.database.session import get_db,SessionLocal
from sqlalchemy import select
from sqlalchemy.exc import OperationalError,SQLAlchemyError,IntegrityError
from app.schema.schema import register_schema,login_schema
from app.models.users import User
from fastapi import HTTPException
from app.security.password_hashing import password_hash
from app.security.jwt import create_access_token
from fastapi import status
import logging
logger=logging.getLogger(__name__)
def register_user(input:register_schema):
    try:
        db=SessionLocal()


        existing_user = db.scalar(
                    select(User).where(User.email == input.email))
        if existing_user:
            raise HTTPException(status_code=409,
                                detail="Try with another email")

        hashed_password = password_hash.hash(input.password)
        user=User(
                username=input.username,
                email=input.email,
                password_hash=hashed_password
            )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("user registered")
        return {"message":"Registered Sucessfully"}
        
    
    
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration conflicts with existing data.",
        ) from exc 
    except OperationalError as exc:
        db.rollback()
        logger.exception("Database operational error during user registration")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The database is temporarily unavailable.",
        ) from exc   
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database connection failure during user registarion")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database operation failed.",
        ) from exc
    
    except HTTPException:
            raise 
    
    except Exception as e:
        logger.exception(f"server error during registration: {e}")
        raise HTTPException(status_code=500,
                            detail=" internal server error ")


    finally:
        db.close()

def autenticate_user(input:login_schema):
    try:
        db=SessionLocal()

        user=db.scalar(select(User).where(User.email==input.email))

        if not user:
            raise HTTPException(status_code=401,
                                detail="invalid credentials")   
        
        if not password_hash.verify(input.password,user.password_hash):
            raise HTTPException(status_code=401,
                                            detail="invalid credentials")
        access_token = create_access_token(
        data={"sub": str(user.id)})       
        logger.info("user authentication sucessfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
   
    except OperationalError as exc:
            db.rollback()
            logger.exception("Database operational error during user authentication")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The database is temporarily unavailable.",
            ) from exc   
    except SQLAlchemyError as exc:
            db.rollback()
            logger.exception("Database connection failure during user authentication")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database operation failed.",
            ) from exc
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"server error during user authentication: {e}")
        raise HTTPException(status_code=500,
             detail="internal server error")
        
    
    finally:
        db.close()
        
        