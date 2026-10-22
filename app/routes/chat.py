from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schema.schema import input_schema
from app.services.llm_service import study_assist
from pydantic import ValidationError
from app.security.auth_dependency import get_current_user
from app.database.session import get_db
from app.models.users import User
import logging
logger=logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat")
def chat(
    prompt: input_schema,
    current_user:User =Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        final_valid_result = study_assist(
            subject=prompt.subject,
            topic=prompt.topic,
            study_mode=prompt.study_mode,
            no_mcqs=prompt.no_mcqs,
            db=db,
            current_user=current_user,
        )
        logger.info("LLM api final response")
        return final_valid_result

   
    except RuntimeError as e:
        logger.exception(f"LLM API runtime error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception(f"LLM API internal server  error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
    



    
