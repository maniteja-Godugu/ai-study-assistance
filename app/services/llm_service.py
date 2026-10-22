
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import logging
from pathlib import Path
from app.schema.schema import response_schema
from pydantic import ValidationError
from app.models.studysession import StudySession
from app.models.users import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError,OperationalError,IntegrityError
from fastapi import HTTPException,status
from openai import (
    OpenAI,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    InternalServerError,
)
import logging
logger=logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


# Module-level singleton client
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not configured")
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


def study_assist(
    subject: str,
    topic: str,
    study_mode: str,
    no_mcqs: int,
    db: Session,
    current_user: User,
) -> response_schema:
    """
    Generate study content via Groq LLM and persist the session.

    Args:
        subject: Subject name (e.g., "Physics")
        topic: Specific topic to study
        study_mode: Exam/preparation mode (e.g., "JEE", "NEET")
        no_mcqs: Number of MCQs to generate
        db: Database session (injected by route handler)
        current_user: Authenticated user (injected by route handler)

    Returns:
        Validated response_schema with definition, explanation, key_points, mcqs

    Raises:
        ValidationError: If LLM response doesn't match schema
        RuntimeError: If API key missing or LLM call fails
    """
    client = _get_client()

    prompt = f"""
        Act as an expert {subject} teacher and study assistant for {study_mode} preparation.

        Your task is to teach the student the given topic in a clear, accurate, structured, and exam-oriented manner.

        Topic: {topic}

        Study Mode: {study_mode}

        Number of MCQs: {no_mcqs}

        Follow these instructions:

        1. Explanation

        * Start with a clear and simple definition of the topic.
        * Explain the concept step by step in language appropriate for the student's study level.
        * Use relevant real-life examples or simple analogies when they help clarify the concept.
        * Focus only on the given topic and closely related concepts necessary to understand it.

        2. Key Points

        * Provide the most important points the student should remember.
        * Focus on points that are relevant to {study_mode} preparation.
        * Keep the key points concise and easy to revise.

        3. MCQs

        * Generate exactly {no_mcqs} multiple-choice questions related to {topic}.
        * Make the questions relevant to {study_mode}.
        * Each question must have exactly 4 options.
        * Ensure the questions test understanding of the topic rather than unrelated information.
        * Avoid ambiguous, duplicate, or poorly worded questions.

        4. Accuracy

        * Provide technically accurate and unambiguous information.
        * Do not invent facts.
        * If a topic has multiple interpretations, use the standard academic interpretation appropriate for {study_mode}.

        5. Scope

        * Stay focused on {topic}.
        * Do not introduce unrelated topics or unnecessary information.
        * Do not include explanations outside the requested response structure.

        Return the response strictly according to the provided structured response format.
    """

    try:
        client = _get_client()

        response = client.responses.create(
            input=prompt,
            model="openai/gpt-oss-120b",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "response_review",
                    "schema": response_schema.model_json_schema(),
                }
            },
        )

    except RuntimeError as exc:
        # For example, _get_client() finds no API key.
        logger.exception(f"LLM api error :{exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service is not configured.",
        ) from exc

    except AuthenticationError as exc:
        logger.exception(f"AI service authentication failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service authentication failed. Please try again later.",
        ) from exc

    except RateLimitError as exc:
        logger.exception(f"The AI service is busy rate limit error")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The AI service is busy. Please try again later.",
        ) from exc

    except APITimeoutError as exc:
        logger.exception(f"The AI service timeout error")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI service took too long to respond. Please try again.",
        ) from exc

    except APIConnectionError as exc:
        logger.exception(f"LLM API connection error {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to the AI service. Please try again later.",
        ) from exc

    except InternalServerError as exc:
        logger.exception(f"LLM API internal server error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable.",
        ) from exc

    except BadRequestError as exc:
        # Often means the provider rejected the request or its parameters.
        # Investigate the request/model configuration on the server.
          
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service could not process this request.",
        ) from exc

    except APIStatusError as exc:
        # Other HTTP errors returned by the provider.
        logger.exception(f"LLM API apistatus error {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service returned an error.",
        ) from exc

    # Stage B: Parse and validate the model response
    try:
        output_text = response.output_text
        logger.info("LLM API response ")

        if not output_text:
            raise ValueError("AI provider returned empty output")

        result = json.loads(output_text)
        valid_result = response_schema.model_validate(result)
        logger.info("LLM API response validated")
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        logger.exception(f"LLM respose validation error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service returned an invalid response. Please try again.",
        ) from exc

    # Stage C: Persist the validated response
    try:
        session = StudySession(
            user_id=current_user.id,
            subject=subject,
            topic=topic,
            study_mode=study_mode,
            generated_content=valid_result.model_dump_json(),
        )

        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info("llm response storing in database")

    except IntegrityError as exc:
        db.rollback()

        # Only use 409 when you have identified a genuine client-data conflict.
        logger.exception(f"Intigrity error during saving LLM response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The generated study content could not be saved.",
        ) from exc

    except OperationalError as exc:
        db.rollback()
        logger.exception(f"operational error during saving LLM response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The database is temporarily unavailable. Please try again.",
        ) from exc

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception(f"database connection error during saving LLM response: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save the generated study content.",
        ) from exc

    return valid_result





#print("explanation: ",valid_result.explanation,"\n")

'''print("key points: ",valid_result.key_points,"\n")
print("Practice Problems:")
for i in range(0,no_mcqs):
    print(i+1,".",valid_result.mcqs[i].Question,"\n")
    for j in range(len(valid_result.mcqs[i].options)):
        char_no=65
        print(chr(char_no+j),".",valid_result.mcqs[i].options[j])
    print("\ncorrect Answer: ",valid_result.mcqs[i].correct_answer)
    print("explanation: ",valid_result.mcqs[i].answer_explaination)
    print()'''

