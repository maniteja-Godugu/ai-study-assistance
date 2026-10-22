
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.studysession import StudySession
from app.models.users import User
from sqlalchemy.exc import SQLAlchemyError,OperationalError
from fastapi import HTTPException,status
import json
import logging
logger=logging.getLogger(__name__)


def get_history(db: Session, current_user: User):
    try:
            stmt = select(StudySession).where(StudySession.user_id == current_user.id)

            history = db.scalars(stmt).all()
            if not history:

                    return "no history found"
            result=[]

            for item in history:
                content=json.loads(item.generated_content)
                history_data={
                            
                            "Date of generation": item.timestamp.isoformat() if item.timestamp else None,
                            "subject": item.subject,
                            "topic": item.topic,
                            "study_mode": item.study_mode,
                            "Defination":content["defination"],
                            "explanation":content["explanation"],
                            "key points":content["key_points"],
                            "mcqs":content["mcqs"]
                        }
                result.append(history_data)

            return result
    except OperationalError as exc:
            db.rollback()
            logger.exception("Database operational error during history check")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The database is temporarily unavailable.",
            ) from exc         
    except SQLAlchemyError as e:
         
         db.rollback()
         logger.exception("Database connection failure during history check")
         raise HTTPException(
            status_code=500,
            detail="A database error occurred. Please try again."
        )
    except (json.JSONDecodeError, ValueError, TypeError, KeyError )as e:
                         logger.exception(f"internal server error during history check {e}")
                         raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Stored study data is invalid."
                )
    except HTTPException:
            raise

 
    except Exception as e:
                logger.exception(f"internal server error during history check {e}")
                raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="internal server error")


