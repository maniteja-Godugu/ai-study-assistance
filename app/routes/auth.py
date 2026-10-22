from fastapi import APIRouter,Depends,Request
from app.schema.schema import register_schema,login_schema
from app.services.auth_service import register_user,autenticate_user
from app.models.users import User
from app.security.auth_dependency import get_current_user
from app.security.rate_limit_slowapi import limiter
import logging
logger=logging.getLogger(__name__)
router=APIRouter() 


@router.get("/")
def home():
    return {
        "message": "Welcome to AI Study Assistant API! #Explore the API",
        "status": "running"
    }


@router.post("/register",status_code=201)
@limiter.limit("10/minute")
def register(input:register_schema,request:Request):
    logger.info("reigister route :user registered successfully ")

    return register_user(input)
    
@router.post("/login",status_code=200) 
@limiter.limit("5/minute")
def login(input:login_schema,request:Request):
    response=autenticate_user(input)
    logger.info("user logged in successfully ")
    return response




@router.get("/me")
def get_my_profile(request:Request,
    current_user: User = Depends(get_current_user)):
    logger.info("user profile")
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username
    }

