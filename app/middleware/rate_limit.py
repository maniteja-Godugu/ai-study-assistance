from fastapi import Request,status
import time
from fastapi.responses import JSONResponse
from app.security.auth_dependency import get_current_user
from fastapi.security import HTTPBearer
import jwt
from app.security.jwt import SECRET_KEY,ALGORITHM
import logging
logger=logging.getLogger(__name__)

chat_counter={}
async def rate_limit_middleware(request:Request,call_next):
    
    
    path=request.url.path


    if path=="/chat":

        
        authorization = request.headers.get("Authorization")

        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated"}
            )

        token = authorization.split(" ", 1)[1]

    
        try:
            payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
            )

            user_id = payload.get("sub")

            if user_id is None:
                return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
                )

        except Exception:
            return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"}
            )

        now=time.monotonic()
        data=chat_counter.get(user_id)

        if data is None:

            data = {
            "min": {
                "count": 0,
                "reset_at": now + 60
            },
            "day": {
                "count": 0,
                "reset_at": now + 86400
            }
            }

        if  now>=data["day"]["reset_at"]:
            data["day"]={"count":0,
                      "reset_at":now+86400
                      
                      }
        if now>=data["min"]["reset_at"]:
            data["min"]={"count":0,
                      "reset_at":now + 60
                        }
            
        if data["day"]["count"]>=20:
            return JSONResponse(
                            status_code=429,
                            content={
                                "detail": "chat rate limit exceeded. Try again tommorow."
                            }
                        )
        if data["min"]["count"]>=5:
                    return JSONResponse(
                                    status_code=429,
                                    content={
                                        "detail": "chat rate limit exceeded. Try again later."
                                    }
                                )
        print("rate limit chat before call_next")
        logger.info("chat route ratelimit middleware befor call next ")
        response=await call_next(request)

        if response.status_code < 400:
             data["day"]["count"]+=1
             data["min"]["count"]+=1

        chat_counter[user_id]=data
        logger.info(" chat route  ratelimit middlewarw after callnext")
        return response
    logger.info(" ratelimit middleware befor call next ")

    response=await call_next(request)
    logger.info(" ratelimit middleware after call next ")
    return response


        


    

    

   