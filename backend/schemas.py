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
    parent_name: str
    child: ChildCreate

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

class QuestionResponse(BaseModel):
    id: int
    order_index: int
    text: str
    image_url: Optional[str] = None 
    option_A: str
    option_B: str
    option_C: str
    
    class Config:
        from_attributes = True

class SuggestedTest(BaseModel):
    skill_category: str
    set_name: str
    is_available: bool

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

class SuggestedGamesResponse(BaseModel):
    status: str  
    message: Optional[str] = None
    games: List[GameSchema] = []
    next_available_date: Optional[datetime] = None

class TestPreviousRequest(BaseModel):
    session_id: int