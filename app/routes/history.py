from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.security.auth_dependency import get_current_user
from app.database.session import get_db
from app.models.users import User
from app.services.history_service import get_history
import logging
logger=logging.getLogger(__name__)
router = APIRouter()


@router.get("/history")
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history_data = get_history(current_user=current_user, db=db)
    logger.info("user chat history")
    return {
        
        "history": history_data,
    }
    