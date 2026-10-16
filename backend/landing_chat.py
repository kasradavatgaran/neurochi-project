"""Durable, idempotent post-registration handoff; no anonymous model calls."""
import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

import models
import schemas
from database import SessionLocal, get_db
from performance import current_metrics

logger = logging.getLogger("rag_service.landing")
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="landing-chat")


class LandingQuestion(BaseModel):
    phone_number: str
    request_id: UUID
    question: str = Field(min_length=1, max_length=1200)
    retry: bool = False


def process_job(job_id, handler):
    current_metrics.set({})
    with SessionLocal() as db:
        claimed = db.query(models.LandingChatJob).filter(
            models.LandingChatJob.id == job_id, models.LandingChatJob.status == "queued",
        ).update({"status": "running", "error": None}, synchronize_session=False)
        db.commit()
        if not claimed:
            return
        job = db.get(models.LandingChatJob, job_id)
        if not job:
            return
        try:
            # A crash after the answer transaction must not cause regeneration.
            answer_exists = db.query(models.ChatMessage.id).filter(
                models.ChatMessage.session_id == job.session_id,
                models.ChatMessage.role == "assistant",
            ).first()
            if not answer_exists:
                phone = db.get(models.User, job.user_id).phone_number
                handler(schemas.ChatRequest(phone_number=phone, message=job.question,
                                            chat_session_id=job.session_id, stream=False), db)
            job = db.get(models.LandingChatJob, job_id)
            if job:
                job.status = "completed"
                db.commit()
        except Exception:
            db.rollback()
            logger.exception("Landing generation failed for job_id=%s", job_id)
            job = db.get(models.LandingChatJob, job_id)
            if job:
                job.status = "failed"
                job.error = "پاسخ آماده نشد؛ سؤال شما محفوظ است و می‌توانید دوباره تلاش کنید."
                db.commit()


def create_router(handler):
    router = APIRouter(tags=["Chat"])

    def owned_user(phone, db):
        user = db.query(models.User).filter(models.User.phone_number == phone).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def payload(job):
        return {"request_id": job.request_id, "chat_session_id": job.session_id,
                "status": job.status, "error": job.error}

    @router.post("/landing-chat", status_code=202)
    def submit(request: LandingQuestion, db=Depends(get_db)):
        user = owned_user(request.phone_number, db)
        if not user.parent_name or not user.children:
            raise HTTPException(status_code=409, detail="ابتدا ثبت‌نام و اطلاعات اولین فرزند را تکمیل کنید.")
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="Question is empty")
        request_id = str(request.request_id)
        job = db.query(models.LandingChatJob).filter_by(user_id=user.id, request_id=request_id).first()
        if not job:
            session = models.ChatSession(user_id=user.id, child_id=None, title=question[:42])
            db.add(session)
            db.flush()
            job = models.LandingChatJob(user_id=user.id, request_id=request_id,
                                        session_id=session.id, question=question, status="queued")
            db.add(job)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                job = db.query(models.LandingChatJob).filter_by(user_id=user.id, request_id=request_id).one()
        elif job.question != question:
            raise HTTPException(status_code=409, detail="Request ID already belongs to a different question")
        elif request.retry and job.status == "failed":
            job.status = "queued"
            job.error = None
            db.commit()
        result = payload(job)
        if job.status == "queued":
            executor.submit(process_job, job.id, handler)
        return result

    @router.get("/landing-chat/{request_id}")
    def status(request_id: UUID, phone_number: str, db=Depends(get_db)):
        user = owned_user(phone_number, db)
        job = db.query(models.LandingChatJob).filter_by(user_id=user.id, request_id=str(request_id)).first()
        if not job:
            raise HTTPException(status_code=404, detail="Question not found")
        return payload(job)

    return router


def resume_jobs(handler):
    with SessionLocal() as db:
        db.query(models.LandingChatJob).filter(models.LandingChatJob.status == "running").update(
            {"status": "queued"}, synchronize_session=False)
        db.commit()
        ids = [row[0] for row in db.query(models.LandingChatJob.id).filter_by(status="queued").all()]
    for job_id in ids:
        executor.submit(process_job, job_id, handler)
