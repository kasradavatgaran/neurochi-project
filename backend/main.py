
import base64
import shutil
import random
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, List
from seed_from_csv import seed_database_from_csv
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func 
from sqlalchemy.orm import joinedload
import wave # 
from fastapi.responses import FileResponse
import hashlib
from google.genai import types
import models, schemas, sms_sender
from seed_games import seed_games_from_excel
from database import engine, get_db
import logging
from process import process_all_txts_in_directory
from retrieve import RetrievalManager, load_cross_encoder_model, re_rank_documents
from generate import  call_gemini_for_analysis,call_gemini_for_transcribe
from google import genai as gen
import google.generativeai as genai
from typing import Dict
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("rag_service.main")


retrieval_manager: RetrievalManager | None = None
cross_encoder = None 
gemini_model = None  

models.Base.metadata.create_all(bind=engine)


SYSTEM_INSTRUCTION = """
شما "نوروچی"، دستیار هوشمند و متخصص رشد کودک هستید.
وظایف اصلی شما:
1. پاسخ‌دهی به سوالات والدین بر اساس "اطلاعات تکمیلی" (Context) ارائه شده.
2. لحن شما باید دلسوزانه، علمی، آرام‌بخش و به زبان فارسی روان باشد.

قوانین بسیار مهم (RAG Rules):
1. **استناد دقیق:** اطلاعات منبع و لینک مقاله در خودِ متنِ "اطلاعات تکمیلی" وجود دارد (نه در متادیتا). شما موظف هستید متن را بررسی کنید و اگر پاسختان بر اساس آن متن است، حتماً نام مقاله و لینک آن را استخراج کرده و در انتهای پاسخ ذکر کنید.
   - فرمت ارجاع: "منبع: [نام مقاله یا سایت] (لینک: [آدرس لینک])"
2. **عدم توهم:** اگر لینک یا منبعی در متن نبود، از خودتان لینک نسازید.
3. **ساختار پاسخ:** پاسخ‌ها کوتاه و پاراگراف‌بندی شده باشند.

*** قانون حیاتی پیشنهاد تست (Smart Suggestion): ***
اگر در صحبت‌های کاربر متوجه شدید که:
- نگران وضعیت رشد فرزندش است (مثلاً می‌گوید "بچه‌ام هنوز راه نمیره" یا "حرف نمیزنه").
- در مورد سن مناسب برای مهارت خاصی سوال می‌پرسد.
- می‌خواهد بداند فرزندش نرمال است یا خیر.
- یا به طور کلی حس کردید زمان مناسبی است که کودک ارزیابی شود.

در انتهای پاسخ خود، حتماً عبارت `[SUGGEST_TESTS]` را قرار دهید. 
این تگ باعث می‌شود دکمه‌های تست به کاربر نمایش داده شود. در متن پاسخ خود به کاربر بگویید که "می‌توانید از تست‌های پایین صفحه استفاده کنید".
"""


GROWTH_ANALYSIS_LOGIC = """
دستورالعمل تحلیل رشد (تو باید دقیقا بر اساس این منطق مشاوره بدهی):
[
  {
    "param": "وزن",
    "condition": "کم شدن تا یک انحراف معیار",
    "age_groups": {
      "0-2m": "در هفته اول ۱۰٪ کاهش طبیعی است. ویزیت روز ۳، ۱۵ و ۳۰ ضروری است. اگر تا ۲ ماهگی ادامه داشت به پزشک مراجعه شود.",
      "2-6m": "بررسی مجدد ۱۵ روز دیگر. علل: شیر ناکافی، رفلاکس. در صورت ادامه به پزشک مراجعه شود.",
      "6-12m": "بررسی مجدد ۱۵ روز دیگر. علل: دندان، انگل، حساسیت. در صورت ادامه به پزشک مراجعه شود.",
      "1-2y": "بررسی مجدد ۱ ماه دیگر. علل: تغذیه، خواب. در صورت ادامه به پزشک مراجعه شود.",
      "2-5y": "بررسی مجدد ۲ ماه دیگر. علل: تغذیه، خواب. در صورت ادامه به پزشک مراجعه شود."
    }
  },
  {
    "param": "وزن",
    "condition": "استپ وزنی (ثابت ماندن)",
    "age_groups": {
      "0-2m": "اگر یک ماه ثابت مانده حتما با پزشک مشورت شود.",
      "2-6m": "اندازه‌گیری مجدد ۲ هفته دیگر. اگر ثابت ماند به پزشک مراجعه شود.",
      "6-12m": "اندازه‌گیری مجدد ۲ هفته دیگر. علل: آلرژی، رفلاکس. اگر ثابت ماند مراجعه شود.",
      "1-2y": "اندازه‌گیری مجدد ۲ هفته دیگر. اگر ثابت ماند مراجعه شود.",
      "2-5y": "اندازه‌گیری مجدد ۱ ماه دیگر. علل: استرس، کالری ناکافی. اگر ثابت ماند مراجعه شود."
    }
  },
  {
    "param": "قد",
    "condition": "توقف رشد قد (ثابت ماندن یا افت از منحنی)",
    "age_groups": {
      "0-3m": "اندازه‌گیری مجدد ۲ ماه دیگر. در صورت اختلاف بیش از ۱ انحراف معیار با وزن، به پزشک مراجعه شود.",
      "3-6m": "در صورت توقف و اختلاف بیش از ۱ انحراف معیار، حتما به پزشک مراجعه شود."
    }
  },
  {
    "param": "دور سر",
    "condition": "رشد ناگهانی (بیش از ۱ انحراف معیار)",
    "action": "نیاز به مراجعه فوری به پزشک است."
  }
]
نکته مهم: برای تشخیص وضعیت، باید داده فعلی را با داده قبلی مقایسه کنی.
"""



UPLOAD_DIR = Path("images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_UPLOAD_DIR = Path("uploaded_audio")
AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TTS_UPLOAD_DIR = Path("uploaded_tts")
TTS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
chat_sessions: Dict[str, genai.ChatSession] = {}
app = FastAPI(title="Nerochi API")
app.mount("/audio", StaticFiles(directory=TTS_UPLOAD_DIR), name="audio")

@app.on_event("startup")
def startup_event():
    """Initializes DB and the entire RAG system when the server starts."""
    global retrieval_manager, cross_encoder, gemini_model
    
    logger.info("Application startup...")
    
    models.Base.metadata.create_all(bind=engine)
    seed_database_from_csv()
    seed_games_from_excel()
    logger.info("Database setup complete.")
    
    try:
        logger.info("Initializing RAG system...")
        docs = process_all_txts_in_directory()
        if not docs:
            raise RuntimeError("No documents were processed. RAG system cannot start.")
        
        retrieval_manager = RetrievalManager()
        retrieval_manager.setup_retrievers(docs)
        
        cross_encoder = load_cross_encoder_model()
        
        logger.info("RAG system initialized successfully.")
        
    except Exception as e:
        logger.critical(f"FATAL: RAG system failed to initialize: {e}", exc_info=True)

        retrieval_manager = None
        cross_encoder = None
        gemini_model = None

    logger.info("Startup complete. Application is ready.")
    

app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

models.Base.metadata.create_all(bind=engine)




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")
def get_or_create_chat_session(user_id: int, child_id: Optional[int], db: Session) -> genai.ChatSession:
    session_key = f"{user_id}_{child_id or 'general'}"
    
    if session_key in chat_sessions:
        logger.info(f"Returning existing chat session for key: {session_key}")
        return chat_sessions[session_key]

    logger.info(f"Creating a new chat session for key: {session_key}")
    
    model = genai.GenerativeModel(
        "gemini-2.5-flash",  
        system_instruction=SYSTEM_INSTRUCTION
    )
    
    initial_history_db = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == user_id,
        models.ChatMessage.child_id == child_id
    ).order_by(models.ChatMessage.timestamp.asc()).limit(20).all()

    gemini_history = []
    for msg in initial_history_db:
        role = "user" if msg.role == "user" else "model"
        gemini_history.append({"role": role, "parts": [{"text": msg.content}]})

    chat_session = model.start_chat(history=gemini_history)
    chat_sessions[session_key] = chat_session
    
    return chat_session

@app.post("/request-otp", status_code=status.HTTP_200_OK, tags=["Authentication"])
def request_otp(user_request: schemas.UserCreate, db: Session = Depends(get_db)):
    otp = str(random.randint(1000, 9999))
    expires_at = datetime.now() + timedelta(minutes=2)

    user = db.query(models.User).filter(models.User.phone_number == user_request.phone_number).first()
    if user:
        user.otp_code = otp
        user.otp_expires_at = expires_at
    else:
        user = models.User(phone_number=user_request.phone_number, otp_code=otp, otp_expires_at=expires_at)
        db.add(user)
    db.commit()
    
    if sms_sender.send_otp_sms(user.phone_number, otp):
        return {"message": "OTP sent successfully."}
    
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP SMS.")

@app.post("/verify-otp", tags=["Authentication"])
def verify_otp(verification_data: schemas.OtpVerify, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone_number == verification_data.phone_number).first()
    
    if not user or user.otp_code != verification_data.otp_code or (user.otp_expires_at and datetime.now() > user.otp_expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="کد تایید نامعتبر یا منقضی شده است.")
    
    user.otp_code = None
    db.commit()
    
    if user.parent_name:
        return {"status": "verified", "action": "login", "user_data": schemas.UserResponse.from_orm(user)}
    else:
        return {"status": "verified", "action": "create_profile", "phone_number": verification_data.phone_number}





@app.get("/me/{phone_number}", response_model=schemas.UserResponse, tags=["Profile"])
def get_user_profile(phone_number: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@app.put("/users/{phone_number}", tags=["Profile"])
def update_user_profile(phone_number: str, parent_name: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.parent_name = parent_name
    db.commit()
    return {"message": "Profile name updated successfully"}

@app.post("/users/{phone_number}/upload-profile-image", tags=["Profile"])
async def upload_profile_image(phone_number: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    file_path = UPLOAD_DIR / f"{phone_number}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    user.profile_image_url = f"images/{file_path.name}"
    db.commit()
    return {"file_url": user.profile_image_url}

def _create_initial_growth_record(child_model: models.Child, child_data: schemas.ChildCreate, db: Session):
    if child_data.birth_height or child_data.birth_weight or child_data.birth_head_circumference:
        initial_record = models.GrowthRecord(
            child_id=child_model.id,
            date=child_model.birth_date, 
            height=child_data.birth_height,
            weight=child_data.birth_weight,
            head_circumference=child_data.birth_head_circumference
        )
        db.add(initial_record)

@app.post("/create-profile", response_model=schemas.UserResponse, tags=["Profile"])
def create_profile(profile: schemas.FullProfileCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone_number == profile.phone_number).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Please verify OTP first.")

    user.parent_name = profile.parent_name
    

    child_core_data = profile.child.dict(exclude={'birth_height', 'birth_weight', 'birth_head_circumference'})
    
    new_child = models.Child(**child_core_data, parent=user)
    db.add(new_child)
    db.flush()

    _create_initial_growth_record(new_child, profile.child, db)

    db.commit()
    db.refresh(user)
    return user

@app.post("/children", response_model=schemas.ChildResponse, tags=["Children"])
def add_child(phone_number: str, child_data: schemas.ChildCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    child_core_data = child_data.dict(exclude={'birth_height', 'birth_weight', 'birth_head_circumference'})
    
    new_child = models.Child(**child_core_data, parent=user)
    db.add(new_child)
    db.flush()

    _create_initial_growth_record(new_child, child_data, db)
    
    db.commit()
    db.refresh(new_child)
    return new_child

@app.put("/children/{child_id}", response_model=schemas.ChildResponse, tags=["Children"])
def update_child(child_id: int, child_update: schemas.ChildCreate, db: Session = Depends(get_db)):
    db_child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not db_child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    
    if db_child.has_conversation_started:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="امکان ویرایش اطلاعات فرزندی که مکالمه‌ای درباره او شروع شده، وجود ندارد.")
    
    update_data = child_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_child, key, value)
        
    db.commit()
    db.refresh(db_child)
    return db_child

@app.delete("/children/{child_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Children"])
def delete_child(child_id: int, db: Session = Depends(get_db)):
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
    
    db.delete(child)
    db.commit()
    return
   

def get_conversation_history_for_child(child_id: int, db: Session) -> str:
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child: return ""

    latest_test_session = db.query(models.ChildTestSession).filter(
        models.ChildTestSession.child_id == child_id,
        models.ChildTestSession.is_completed == True
    ).order_by(models.ChildTestSession.start_time.desc()).first()

    if not latest_test_session:
        return f"تاریخچه اولیه برای کودک '{child.name}': هنوز هیچ تستی تکمیل نشده است."

    skill_category = latest_test_session.question_set.skill_category
    
    test_answers = db.query(models.TestAnswer).filter(
        models.TestAnswer.session_id == latest_test_session.id
    ).options(joinedload(models.TestAnswer.question)).all()
    
    history_text = f"شما در حال گفتگو با والد کودک '{child.name}' هستید. این خلاصه‌ای از آخرین فعالیت‌های ثبت شده برای مهارت '{skill_category}' است:\n"
    
    test_summary = "خلاصه تست:\n"
    for ans in test_answers:
        test_summary += f"- سوال: '{ans.question.text}' -> پاسخ: '{ans.chosen_option}'\n"

    game_responses = db.query(models.GameResponse).filter(
        models.GameResponse.child_id == child_id,
        models.GameResponse.timestamp >= latest_test_session.start_time
    ).join(models.Game).filter(
        models.Game.skill_category == skill_category
    ).options(joinedload(models.GameResponse.game)).all()
    
    game_summary = "خلاصه بازی‌ها:\n"
    if game_responses:
        for resp in game_responses:
            user_response = "توانست" if resp.response == 'can_do' else "نتوانست"
            game_summary += f"- بازی: '{resp.game.title}' -> نتیجه: {user_response}\n"
    
    return history_text + test_summary + game_summary


@app.post("/chat", tags=["Chat"])
async def handle_chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone_number == request.phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    
    if request.message.startswith("/start_test_now"):
        try:
            _, skill_category = request.message.split(' ', 1)
            skill_category = skill_category.strip()
        except ValueError:
            return {"type": "chat_message", "response": "فرمت دستور تست نامعتبر است."}
        child = db.query(models.Child).filter(models.Child.id == request.child_id).first()
        age_days = calculate_age_in_days(child.birth_date)
        question_set = db.query(models.SkillQuestionSet).filter(
            models.SkillQuestionSet.skill_category == skill_category,
            models.SkillQuestionSet.min_age_days <= age_days,
            models.SkillQuestionSet.max_age_days >= age_days
        ).first()
        if question_set:
            first_question = db.query(models.Question).filter(
                models.Question.question_set_id == question_set.id
            ).order_by(models.Question.order_index.asc()).first()
            if first_question:
                session = models.ChildTestSession(
                    child_id=child.id,
                    question_set_id=question_set.id,
                    next_question_index=first_question.order_index
                )
                db.add(session)
                db.commit()
                return {"type": "start_test", "session_id": session.id, "question": schemas.QuestionResponse.from_orm(first_question)}
            else:
                return {"type": "chat_message", "response": f"هیچ سوالی برای تست '{skill_category}' در این رده سنی یافت نشد."}
        else:
            return {"type": "chat_message", "response": f"متاسفانه تستی برای مهارت '{skill_category}' در سن فعلی {child.name} موجود نیست."}
    
    if request.message.startswith("کاربر فرزند"): 
        logger.info(f"System message received, skipping RAG/Gemini call: '{request.message}'")

        if request.child_id:
            child = db.query(models.Child).filter(models.Child.id == request.child_id).first()
            if child and not child.has_conversation_started:
                child.has_conversation_started = True
                db.commit()
        return {"type": "system_ack", "response": "Acknowledged"}
    
    if request.message.startswith("سلام، در مورد"): 
        logger.info(f"System message received, skipping RAG/Gemini call: '{request.message}'")

        if request.child_id:
            child = db.query(models.Child).filter(models.Child.id == request.child_id).first()
            if child and not child.has_conversation_started:
                child.has_conversation_started = True
                db.commit()
        return {"type": "system_ack", "response": "Acknowledged"}
    chat_session = get_or_create_chat_session(user.id, request.child_id, db)
    rag_context = ""
    try:
        retrieved_docs = retrieval_manager.retrieve_documents(request.message)
        reranked_docs = re_rank_documents(cross_encoder, request.message, retrieved_docs, top_n=10)
        if reranked_docs:
            rag_context = reranked_docs[0].page_content
    except Exception as e:
        logger.error(f"Error during RAG for chat: {e}")

    final_prompt = request.message
    if rag_context:
        final_prompt = f"""
        از متن‌های زیر به عنوان "دانش تکمیلی" برای پاسخ به سوال من استفاده کن.
        
        *** نکته مهم: در متن‌های زیر، نام مقاله و لینک منبع وجود دارد. آنها را پیدا کن و در انتهای پاسخ به کاربر نمایش بده. ***

        --- دانش تکمیلی ---
        {rag_context}
        ---
        
        سوال اصلی من این است: {request.message}
        """

    try:
        response = await chat_session.send_message_async(final_prompt)
        raw_bot_response = response.text
    except Exception as e:
        logger.error(f"Error sending message to Gemini session: {e}")
        bot_response_text = "متاسفانه در حال حاضر امکان پاسخگویی وجود ندارد."
        session_key = f"{user.id}_{request.child_id or 'general'}"
        if session_key in chat_sessions:
            del chat_sessions[session_key]
    show_tests = False
    bot_response_text = raw_bot_response

    if "[SUGGEST_TESTS]" in raw_bot_response:
        show_tests = True
        bot_response_text = raw_bot_response.replace("[SUGGEST_TESTS]", "").strip()
    db.add(models.ChatMessage(user_id=user.id, child_id=request.child_id, role='assistant', content=bot_response_text))
    db.commit()
    db.add(models.ChatMessage(user_id=user.id, child_id=request.child_id, role='user', content=request.message))
    db.flush()

    return {
        "type": "chat_message", 
        "response": bot_response_text, 
        "show_tests": show_tests
    }


def calculate_age_in_days(birth_date: date) -> int:
    return (date.today() - birth_date).days



@app.get("/children/{child_id}/growth-analysis", tags=["Growth Analysis"])
def get_growth_analysis(child_id: int, db: Session = Depends(get_db)):
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    last_record = db.query(models.GrowthRecord).filter(models.GrowthRecord.child_id == child_id).order_by(models.GrowthRecord.date.desc()).first()
    if not last_record:
        return {"message": "هیچ رکورد رشدی برای این کودک ثبت نشده است."}

    age_days = calculate_age_in_days(child.birth_date)
    analysis = {}
    return {
        "child_info": schemas.ChildResponse.from_orm(child),
        "point_in_time_analysis": analysis,
        "time_series_analysis": "این بخش در حال توسعه است."
    }
def calculate_age_in_days(birth_date: date) -> int:
    """تابع کمکی: محاسبه سن کودک به روز."""
    return (date.today() - birth_date).days


def seed_test_data(db: Session):
    TEST_IMAGES_DIR = UPLOAD_DIR / "test_images"
    TEST_IMAGES_DIR.mkdir(exist_ok=True)

    if db.query(models.SkillQuestionSet).count() == 0:
        print("Seeding database with test data...")
        test_set = models.SkillQuestionSet(
            name="ASQ-3_4m_FineMotor",
            skill_category="مهارت های حرکتی ریز",
            min_age_days=60,  
            max_age_days=150, 
        )
        db.add(test_set)
        db.flush()
        db.add(models.Question(
            question_set_id=test_set.id, order_index=1,
            text="آیا کودک وقتی به پشت خوابیده، دست‌هایش را به هم می‌زند؟",
            image_url="images/test_images/t1_q1.jpg", 
            score_A=10.0, score_B=5.0, score_C=0.0
        ))
        db.add(models.Question(
            question_set_id=test_set.id, order_index=2,
            text="آیا کودک شیئی را که شما به او می‌دهید، نگه می‌دارد؟",
            image_url="images/test_images/t1_q2.jpg",
            score_A=10.0, score_B=5.0, score_C=0.0
        ))
        test_set_2 = models.SkillQuestionSet(
            name="ASQ-3_9m_ProblemSolving",
            skill_category="حل مسئله",
            min_age_days=210,  
            max_age_days=300, 
        )
        db.add(test_set_2)
        db.flush()
        db.add(models.Question(
            question_set_id=test_set_2.id, order_index=1,
            text="آیا کودک برای برداشتن اسباب‌بازی، مانع (پارچه یا پتو) را کنار می‌زند؟",
            image_url="images/test_images/t2_q1.jpg",
            score_A=10.0, score_B=5.0, score_C=0.0
        ))

        db.commit()
        print("Test data seeded successfully.")



@app.get("/children/{child_id}/suggested-tests", response_model=List[schemas.SuggestedTest], tags=["Skill Tests"])
def get_suggested_tests(child_id: int, db: Session = Depends(get_db)):
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    age_days = calculate_age_in_days(child.birth_date)
    suggested = []
    
    available_sets = db.query(models.SkillQuestionSet).filter(
        models.SkillQuestionSet.min_age_days <= age_days,
        models.SkillQuestionSet.max_age_days >= age_days
    ).all()
    last_completed_sessions = db.query(
        models.ChildTestSession.question_set_id,
        func.max(models.ChildTestSession.start_time)
    ).filter(
        models.ChildTestSession.child_id == child_id,
        models.ChildTestSession.is_completed == True
    ).group_by(models.ChildTestSession.question_set_id).all()
    last_completion_times = {q_id: max_time for q_id, max_time in last_completed_sessions}
    
    for set_ in available_sets:
        is_available = True
        last_time = last_completion_times.get(set_.id)
        
        if last_time:
            if datetime.utcnow() - last_time < timedelta(days=60):
                is_available = False
        
        suggested.append(schemas.SuggestedTest(
            skill_category=set_.skill_category,
            set_name=set_.name, 
            is_available=is_available
        ))

    return suggested




def get_score_status_and_suggestion(score_percentage: float, skill_category: str) -> dict:
    """بر اساس درصد امتیاز، وضعیت و نیاز به بازی را برمی‌گرداند."""
    print(score_percentage)
    if score_percentage >= 85:
        return {"status": "عالی", "color": "green", "suggestion": f"رشد {skill_category} در کودک شما عالی است! نیازی به انجام بازی‌های بیشتر نیست.", "needs_games": False}
    elif 60 <= score_percentage < 85:
        return {"status": "نرمال", "color": "blue", "suggestion": f"رشد {skill_category} در محدوده طبیعی قرار دارد.", "needs_games": False}
    else: 
        status = "نیاز به توجه" if 40 <= score_percentage < 60 else "نیاز به بررسی"
        color = "yellow" if 40 <= score_percentage < 60 else "red"
        return {
            "status": status, 
            "color": color, 
            "suggestion": f"به نظر می‌رسد مهارت '{skill_category}' نیاز به تمرین بیشتری دارد. ما چند بازی سرگرم‌کننده برای شما آماده کرده‌ایم.", 
            "needs_games": True 
        }
    
@app.post("/tests/answer", response_model=schemas.CurrentQuestionResponse, tags=["Skill Tests"])
def submit_test_answer(request: schemas.TestAnswerRequest, db: Session = Depends(get_db)):
    session = db.query(models.ChildTestSession).filter(models.ChildTestSession.id == request.session_id).first()
    if not session or session.is_completed:
        raise HTTPException(status_code=400, detail="جلسه تست یافت نشد یا تکمیل شده است.")
    question_set = session.question_set
    current_question = db.query(models.Question).filter(
        models.Question.question_set_id == question_set.id,
        models.Question.order_index == session.next_question_index
    ).first()
    score_map = {'A': current_question.score_A, 'B': current_question.score_B, 'C': current_question.score_C}
    score = score_map.get(request.answer_choice.upper())
    db.add(models.TestAnswer(session_id=session.id, question_id=current_question.id, chosen_option=request.answer_choice.upper(), score_awarded=score))
    
    next_question = db.query(models.Question).filter(
        models.Question.question_set_id == question_set.id,
        models.Question.order_index > session.next_question_index
    ).order_by(models.Question.order_index.asc()).first()
    
    if not next_question:
        session.is_completed = True
        total_score = db.query(func.sum(models.TestAnswer.score_awarded)).filter(models.TestAnswer.session_id == session.id).scalar() or 0.0
        session.total_score = total_score
        
        all_questions = db.query(models.Question).filter(models.Question.question_set_id == question_set.id).all()
        max_possible_score = sum(q.score_A for q in all_questions)

        score_percentage = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        result_details = get_score_status_and_suggestion(score_percentage, question_set.skill_category)
        
        db.commit()

        return schemas.CurrentQuestionResponse(
            session_id=session.id,
            is_last_question=True,
            final_result={
                "title": f"تست '{question_set.skill_category}' برای {session.child.name} تمام شد!",
                "score": total_score,
                "max_score": max_possible_score,
                "status": result_details["status"],
                "status_color": result_details["color"],
                "suggestion": result_details["suggestion"],
                "needs_games": result_details["needs_games"] # <--- این فیلد مهم است
            }
        )
    else:
        session.next_question_index = next_question.order_index
        db.commit()
        return schemas.CurrentQuestionResponse(
            session_id=session.id, is_last_question=False, question=schemas.QuestionResponse.from_orm(next_question))

@app.get("/children/{child_id}/suggested-games", response_model=schemas.SuggestedGamesResponse, tags=["Games"])
def get_suggested_games(child_id: int, skill_category: str, db: Session = Depends(get_db)):

    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    last_played = db.query(models.GameResponse).join(models.Game).filter(
        models.GameResponse.child_id == child_id,
        models.Game.skill_category == skill_category,
        models.GameResponse.timestamp > seven_days_ago
    ).order_by(models.GameResponse.timestamp.desc()).first()

    if last_played:
        unlock_date = last_played.timestamp + timedelta(days=7)
        days_left = (unlock_date - datetime.now()).days
        return schemas.SuggestedGamesResponse(
            status="locked",
            message=f"شما تمرینات این هفته را انجام داده‌اید. لطفاً {days_left + 1} روز دیگر برای بازی‌های جدید برگردید.",
            games=[],
            next_available_date=unlock_date
        )

    age_days = calculate_age_in_days(child.birth_date)
    
    available_games = db.query(models.Game).filter(
        models.Game.skill_category == skill_category,
        models.Game.min_age_days <= age_days,
        models.Game.max_age_days >= age_days
    ).all()
    
    if not available_games:
        return schemas.SuggestedGamesResponse(
            status="empty",
            message="متاسفانه بازی مناسبی برای این سن یافت نشد.",
            games=[]
        )
    
    count_to_select = min(len(available_games), 5)
    selected_games = random.sample(available_games, count_to_select)
    
    return schemas.SuggestedGamesResponse(
        status="available",
        games=selected_games
    )


@app.post("/games/answer", status_code=status.HTTP_201_CREATED, tags=["Games"])
def submit_game_answer(answer: schemas.GameAnswerRequest, db: Session = Depends(get_db)):

    child = db.query(models.Child).filter(models.Child.id == answer.child_id).first()
    game = db.query(models.Game).filter(models.Game.id == answer.game_id).first()

    if not child or not game:
        raise HTTPException(status_code=404, detail="Child or Game not found")
    
    if answer.response not in ['can_do', 'cannot_do']:
        raise HTTPException(status_code=400, detail="Invalid response value.")

    new_response = models.GameResponse(
        child_id=answer.child_id,
        game_id=answer.game_id,
        response=answer.response
    )
    db.add(new_response)
    db.commit()
    
    return {"message": "Answer submitted successfully."}




@app.get("/children/{child_id}/final-analysis", tags=["Analysis"])
def get_final_analysis_for_skill(child_id: int, skill_category: str, db: Session = Depends(get_db)):

    try:
        if not all([retrieval_manager, cross_encoder]):
            raise HTTPException(status_code=503, detail="RAG system is not available or failed to initialize.")
            
        child = db.query(models.Child).filter(models.Child.id == child_id).first()
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")

        latest_test_session = db.query(models.ChildTestSession).join(models.SkillQuestionSet).filter(
            models.ChildTestSession.child_id == child_id,
            models.SkillQuestionSet.skill_category == skill_category,
            models.ChildTestSession.is_completed == True
        ).order_by(models.ChildTestSession.start_time.desc()).first()

        if not latest_test_session:
            raise HTTPException(status_code=404, detail=f"No completed test session found for skill: {skill_category}")

        ANSWER_MAP = {'A': 'بله', 'B': 'گاهی', 'C': 'هنوز نه'}
        test_answers = db.query(models.TestAnswer).filter(
            models.TestAnswer.session_id == latest_test_session.id
        ).options(joinedload(models.TestAnswer.question)).all()
        
        test_summary = f"خلاصه تست مهارت '{skill_category}' برای کودک '{child.name}':\n"
        for ans in test_answers:
            question_text = ans.question.text
            chosen_option_persian = ANSWER_MAP.get(ans.chosen_option, ans.chosen_option)
            test_summary += f"- سوال: '{question_text}' -> پاسخ: '{chosen_option_persian}'\n"

        game_responses = db.query(models.GameResponse).filter(
            models.GameResponse.child_id == child_id,
            models.GameResponse.timestamp >= latest_test_session.start_time
        ).join(models.Game).filter(
            models.Game.skill_category == skill_category
        ).options(joinedload(models.GameResponse.game)).all()

        game_summary = "\nخلاصه بازی‌های انجام شده برای تقویت این مهارت:\n"
        if game_responses:
            for resp in game_responses:
                game_title = resp.game.title
                game_description = resp.game.description
                user_response = "توانست انجام دهد" if resp.response == 'can_do' else "نتوانست انجام دهد"
                game_summary += f"- بازی: '{game_title}' (توضیحات: {game_description}) -> نتیجه: کودک '{user_response}'\n"
        else:
            game_summary += "هیچ بازی‌ای پس از تست انجام نشده است.\n"
        
        query_generation_prompt = f"""
        شما یک متخصص جستجو هستید. بر اساس خلاصه وضعیت یک کودک در مهارت '{skill_category}'، یک کوئری جستجوی کوتاه و مؤثر به زبان فارسی تولید کن.
        این کوئری برای یافتن مقالات و راهکارهای عملی از یک پایگاه دانش استفاده خواهد شد.
        فقط و فقط خود کوئری را خروجی بده و هیچ متن اضافه‌ای ننویس.
        
        خلاصه وضعیت کودک:
        {test_summary}
        {game_summary}

        کوئری جستجوی پیشنهادی شما (فقط یک عبارت یا سوال کوتاه):
        """
        query=call_gemini_for_analysis( query_generation_prompt)
        rag_context = "\nاطلاعات تکمیلی و راهکارهای علمی از اسناد برای تقویت این مهارت:\n"
            
        retrieved_docs = retrieval_manager.retrieve_documents(query)
            
        reranked_docs = re_rank_documents(cross_encoder, query, retrieved_docs, top_n=2)

        if reranked_docs:
            for i, doc in enumerate(reranked_docs):
                rag_context += f"{i+1}. از منبع '{doc.metadata.get('source_file', 'ناشناخته')}':\n\"{doc.page_content}\"\n"
        else:
            rag_context += "نکته تکمیلی خاصی در اسناد یافت نشد.\n"
    except Exception as e:
        logger.error(f"Error during RAG process for skill '{skill_category}': {e}")
        rag_context += "خطا در پردازش اطلاعات تکمیلی.\n"

    prompt = f"""
    شما یک متخصص رشد کودک هستید. یک والد اطلاعات زیر را در مورد فرزندش برای مهارت '{skill_category}' ثبت کرده است.
    وظیفه شما این است که یک تحلیل کوتاه، مفید و دلگرم‌کننده در سه بخش (نقاط قوت، نقاط قابل بهبود، پیشنهاد نوروچی) ارائه دهید.
    لحن شما باید دوستانه، مثبت و راهنما باشد. از اصطلاحات پیچیده پرهیز کنید.

    بخش اول: اطلاعات ثبت شده از کودک:
    {test_summary}
    {game_summary}

    بخش دوم: {rag_context}

    دستورالعمل تحلیل:
    - برای بخش "نقاط قوت" و "نقاط قابل بهبود"، فقط از "بخش اول: اطلاعات ثبت شده از کودک" استفاده کن.
    - برای بخش "پیشنهاد نوروچی"، تحلیل خود از داده‌های کودک را با راهکارهای علمی موجود در "بخش دوم: اطلاعات تکمیلی" ترکیب کن تا پیشنهاداتی عملی، خلاقانه و مبتنی بر شواهد به والدین ارائه دهی. حتما به نکات استخراج شده از اسناد اشاره کن.

    لطفا تحلیل خود را در سه بخش مجزا ارائه دهید:
    """
    
    logger.info(f"--- FINAL PROMPT FOR GEMINI (with RAG) ---\n{prompt}\n-------------------------")
    
    analysis_result = call_gemini_for_analysis( prompt)
    
    return {"analysis": analysis_result}



@app.post("/transcribe-audio", tags=["Chat"])
async def handle_audio_upload(phone_number: str, child_id: Optional[int] = None, file: UploadFile = File(...), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_path = AUDIO_UPLOAD_DIR / f"{phone_number}_{datetime.now().timestamp()}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    transcribed_text = await call_gemini_for_transcribe(file_path)
    
    file_path.unlink()

    if not transcribed_text:
        raise HTTPException(status_code=400, detail="Could not understand the audio.")

    chat_request = schemas.ChatRequest(
        phone_number=phone_number,
        message=transcribed_text,
        child_id=child_id
    )
    chat_session = get_or_create_chat_session(user.id, child_id, db)
    rag_context = ""
    try:
        retrieved_docs = retrieval_manager.retrieve_documents(transcribed_text)
        reranked_docs = re_rank_documents(cross_encoder, transcribed_text, retrieved_docs, top_n=3)
        if reranked_docs:
            context_parts = []
            for doc in reranked_docs:
                title = doc.metadata.get('title', 'بدون عنوان')
                url = doc.metadata.get('url', '') 
                
                link_text = f"لینک: {url}" if url else "لینک: موجود نیست"

                doc_text = f"""
                --- سند یافت شده ---
                عنوان: {title}
                {link_text}
                متن: {doc.page_content}
                --------------------
                """
                context_parts.append(doc_text)
            
            rag_context = "\n".join(context_parts)
    except Exception as e:
        logger.error(f"Error during RAG for chat: {e}")

    final_prompt = transcribed_text
    if rag_context:
        final_prompt = f"""
        از اطلاعات زیر به عنوان دانش تکمیلی برای پاسخ به سوال من استفاده کن.
        --- دانش تکمیلی ---
        {rag_context}
        ---
        سوال اصلی من این است: {transcribed_text}
        """

    try:
        response = await chat_session.send_message_async(final_prompt)
        raw_bot_response = response.text
    except Exception as e:
        logger.error(f"Error sending message to Gemini session: {e}")
        bot_response_text = "متاسفانه در حال حاضر امکان پاسخگویی وجود ندارد."
        session_key = f"{user.id}_{child_id or 'general'}"
        if session_key in chat_sessions:
            del chat_sessions[session_key]
    show_tests = False
    bot_response_text = raw_bot_response

    if "[SUGGEST_TESTS]" in raw_bot_response:
        show_tests = True
        bot_response_text = raw_bot_response.replace("[SUGGEST_TESTS]", "").strip()
    db.add(models.ChatMessage(user_id=user.id, child_id=child_id, role='assistant', content=bot_response_text))
    db.commit()

    return {
        "transcribed_text": transcribed_text,
        "bot_response": bot_response_text,
        "show_tests": show_tests  
    }

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(str(filename), "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

@app.post("/text-to-speech", tags=["TTS"])
async def text_to_speech_handler(request: schemas.TTSRequest):
    """
    متن ورودی را به صوت تبدیل کرده و آدرس فایل صوتی را برمی‌گرداند.
    """
    try:
        logger.info(f"Received TTS request for text: '{request.text[:30]}...'")
        
        text_hash = hashlib.sha1(request.text.encode('utf-8')).hexdigest()
        file_name = f"{text_hash}.wav"
        file_path = TTS_UPLOAD_DIR / file_name

        if file_path.exists():
            logger.info(f"Returning cached TTS file: {file_name}")
            return {"audio_url": f"/audio/{file_name}"}


        client = gen.Client()

        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=request.text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name='Kore',
                        )
                    )
                ),
            )
        )

        raw_data = response.candidates[0].content.parts[0].inline_data.data

        try:

            decoded_data = base64.b64decode(raw_data)
        except Exception:
            decoded_data = raw_data

        wave_file(file_path, decoded_data, rate=24000)
        
        logger.info(f"Successfully saved TTS audio to {file_path}")
        return {"audio_url": f"/audio/{file_name}"}

    except Exception as e:
        logger.error(f"Error in TTS generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate audio from text.")
    
@app.post("/children/{child_id}/growth-records", response_model=schemas.GrowthRecordResponse, tags=["Growth Analysis"])
def add_growth_record(child_id: int, record_data: schemas.GrowthRecordCreate, db: Session = Depends(get_db)):
    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
        
    new_record = models.GrowthRecord(
        child_id=child_id,
        date=datetime.now(), 
        **record_data.dict()
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@app.get("/children/{child_id}/growth-chart", response_model=schemas.GrowthChartResponse, tags=["Growth Analysis"])
def get_growth_chart_data(child_id: int, db: Session = Depends(get_db)):

    child = db.query(models.Child).filter(models.Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    growth_records = db.query(models.GrowthRecord).filter(
        models.GrowthRecord.child_id == child_id
    ).order_by(models.GrowthRecord.date.asc()).all()

    analysis = "برای دریافت تحلیل، لطفا اطلاعات رشد (قد، وزن، دور سر) را ثبت کنید."
    
    if len(growth_records) >= 1:
        latest = growth_records[-1]
        previous = growth_records[-2] if len(growth_records) > 1 else None
        
        age_days = (latest.date.date() - child.birth_date).days
        age_months = age_days / 30
        
        prompt = f"""
        نقش: متخصص تحلیل نمودار رشد کودکان (نوروچی).
        
        اطلاعات کودک:
        - سن: {age_days} روز (حدود {int(age_months)} ماه)
        - جنسیت: {child.gender}
        
        داده‌های فعلی (امروز):
        - وزن: {latest.weight} | قد: {latest.height} | دور سر: {latest.head_circumference}
        
        داده‌های قبلی (در صورت وجود):
        {f"- وزن: {previous.weight} | قد: {previous.height} | دور سر: {previous.head_circumference}" if previous else "این اولین رکورد است."}
        
        دستور کار:
        با استفاده از "جدول منطق تحلیل" زیر، وضعیت کودک را بررسی کن و دقیقا متن توصیه شده در جدول را برای والدین بنویس.
        اگر داده کافی نیست، طبق جدول بگو اطلاعات کم است.
        
        {GROWTH_ANALYSIS_LOGIC}
        
        خروجی: فقط متن تحلیل نهایی را به زبان فارسی و با لحن محترمانه بنویس. تحلیل را به تفکیک پارامتر (وزن، قد، دور سر) ارائه بده.
        """
        
        try:
            analysis = call_gemini_for_analysis(prompt)
        except Exception as e:
            logger.error(f"Error analysis: {e}")
            analysis = "سیستم هوشمند موقتا در دسترس نیست، اما نمودارها دقیق هستند."

    return {
        "records": growth_records,
        "analysis": analysis
    }

