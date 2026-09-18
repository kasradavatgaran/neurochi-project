from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

class GrowthRecordBase(BaseModel):
    height: Optional[float] = Field(None, description="قد به سانتی‌متر")
    weight: Optional[float] = Field(None, description="وزن به کیلوگرم")
    head_circumference: Optional[float] = Field(None, description="دور سر به سانتی‌متر")

class GrowthRecordCreate(GrowthRecordBase):
    pass

class GrowthRecordResponse(GrowthRecordBase):
    id: int
    date: datetime  
    
    class Config:
        from_attributes = True

class ChildBase(BaseModel):
    name: str
    birth_date: date
    gender: str

class ChildCreate(ChildBase):
    gestation_week: int
    birth_height: Optional[float] = Field(None, description="قد در زمان تولد به سانتی‌متر")
    birth_weight: Optional[float] = Field(None, description="وزن در زمان تولد به کیلوگرم")
    birth_head_circumference: Optional[float] = Field(None, description="دور سر در زمان تولد به سانتی‌متر")

class ChildResponse(ChildBase):
    id: int
    has_conversation_started: bool
    growth_records: List[GrowthRecordResponse] = []
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    phone_number: str

class UserCreate(UserBase):
    pass

class FullProfileCreate(BaseModel):
    phone_number: str
    parent_name: str = Field(min_length=1)
    # Kept optional for the post-OTP flow.  Older clients can still create a
    # first child in the same request.
    child: Optional[ChildCreate] = None

class UserResponse(BaseModel):
    id: int
    phone_number: str
    parent_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    children: List[ChildResponse] = []
    
    class Config:
        from_attributes = True

class OtpVerify(BaseModel):
    phone_number: str
    otp_code: str

class ChatRequest(BaseModel):
    phone_number: str
    message: str
    child_id: Optional[int] = None
    chat_session_id: Optional[int] = None
    stream: bool = False
    context: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: List[dict] = []
    sources_html: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class QuestionResponse(BaseModel):
    id: int
    order_index: int
    text: str
    image_url: Optional[str] = None 
    option_A: str
    option_B: str
    option_C: str
    selected_option: Optional[str] = None
    selected_option_text: Optional[str] = None
    
    class Config:
        from_attributes = True

class SuggestedTest(BaseModel):
    skill_category: str
    set_name: str
    is_available: bool
    min_age_days: Optional[int] = None
    max_age_days: Optional[int] = None
    last_completed_at: Optional[datetime] = None
    question_count: int = 0


class TestPreviewResponse(BaseModel):
    child_id: int
    child_name: str
    skill_category: str
    set_name: str
    age_days: int
    age_months: float
    min_age_days: int
    max_age_days: int
    question_count: int
    first_question_order: int = 1
    intro: str
    last_session_id: Optional[int] = None
    last_completed_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_score: Optional[float] = None
    last_answers: List[dict] = []

class ChatSessionResponse(BaseModel):
    id: int
    child_id: Optional[int] = None
    title: str
    summary_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

class ChatSessionCreateRequest(BaseModel):
    title: Optional[str] = None


class TestStartRequest(BaseModel):
    skill_category: str
    new_session: bool = False


class TestSessionResponse(BaseModel):
    session_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    selected_answers: dict = {}

class TestAnswerRequest(BaseModel):
    session_id: int
    answer_choice: str

class FinalResultResponse(BaseModel):
    title: str
    score: float
    max_score: float
    status: str
    status_color: str
    suggestion: str
    needs_games: bool

class CurrentQuestionResponse(BaseModel):
    session_id: int
    is_last_question: bool
    question: Optional[QuestionResponse] = None
    final_result: Optional[FinalResultResponse] = None
    selected_option: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class GameSchema(BaseModel):
    id: int
    title: str
    description: str
    skill_category: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class GameAnswerRequest(BaseModel):
    child_id: int
    game_id: int
    response: str
    
class TTSRequest(BaseModel):
    text: str

class GrowthChartResponse(BaseModel):
    records: List[GrowthRecordResponse]
    analysis: str
    standard_analysis: str = ""
    trend_analysis: str = ""
    metric_analyses: dict = {}
    sex: str = ""
    age_days: int = 0
    age_range: str = ""
    standards_available: bool = False
    standards: dict = {}

class SuggestedGamesResponse(BaseModel):
    status: str  
    message: Optional[str] = None
    games: List[GameSchema] = []
    next_available_date: Optional[datetime] = None
    test_status: Optional[str] = None
    test_completed_at: Optional[datetime] = None

class TestPreviousRequest(BaseModel):
    session_id: int
