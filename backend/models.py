

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text,Date
from sqlalchemy.orm import relationship
from database import Base  
from datetime import datetime
from typing import List 
from pydantic import BaseModel 



class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    parent_name = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user") 

class Child(Base):
    __tablename__ = "children"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    birth_date = Column(Date)
    gender = Column(String)
    gestation_week = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    has_conversation_started = Column(Boolean, default=False, nullable=False)
    
    parent = relationship("User", back_populates="children")
    growth_records = relationship("GrowthRecord", back_populates="child", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    child_id = Column(Integer, ForeignKey("children.id"), nullable=True) 
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_messages")

class GrowthRecord(Base):
    __tablename__ = "growth_records"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    date = Column(DateTime, default=datetime.utcnow)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    head_circumference = Column(Float, nullable=True)
    child = relationship("Child", back_populates="growth_records")

class GrowthStandard(Base):
    __tablename__ = "growth_standards"
    id = Column(Integer, primary_key=True)
    metric = Column(String) 
    gender = Column(String) 
    age_days = Column(Integer)
    mean = Column(Float) 
    sd_plus_1 = Column(Float)
    sd_minus_1 = Column(Float)
    sd_plus_2 = Column(Float)
    sd_minus_2 = Column(Float)

class SkillQuestionSet(Base):
    __tablename__ = "skill_question_sets"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, unique=True)
    skill_category = Column(String, index=True) 
    min_age_days = Column(Integer)
    max_age_days = Column(Integer)
    questions = relationship("Question", back_populates="question_set", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    question_set_id = Column(Integer, ForeignKey("skill_question_sets.id"))
    order_index = Column(Integer)
    text = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    option_A = Column(String, default="بله")
    score_A = Column(Float, default=10.0)
    option_B = Column(String, default="گاهی")
    score_B = Column(Float, default=5.0)
    option_C = Column(String, default="هنوز نه")
    score_C = Column(Float, default=0.0)
    question_set = relationship("SkillQuestionSet", back_populates="questions")

class ChildTestSession(Base):
    __tablename__ = "child_test_sessions"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    question_set_id = Column(Integer, ForeignKey("skill_question_sets.id"))
    start_time = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    total_score = Column(Float, default=0.0)
    next_question_index = Column(Integer, default=1)
    child = relationship("Child")
    question_set = relationship("SkillQuestionSet")
    answers = relationship("TestAnswer", back_populates="session", cascade="all, delete-orphan")
    
class TestAnswer(Base):
    __tablename__ = "test_answers"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("child_test_sessions.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    chosen_option = Column(String)
    score_awarded = Column(Float)
    session = relationship("ChildTestSession", back_populates="answers")
    question = relationship("Question")

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    skill_category = Column(String, index=True)
    min_age_days = Column(Integer)
    max_age_days = Column(Integer)
    image_url = Column(String, nullable=True)

class GameResponse(Base):
    __tablename__ = "game_responses"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("children.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    child = relationship("Child")
    game = relationship("Game")


class RAGQueryRequest(BaseModel): 
    query: str
    top_n: int = 5

class SourceDocument(BaseModel): 
    source_file: str
    content: str
    
class RAGQueryResponse(BaseModel): 
    answer: str
    sources: List[SourceDocument]