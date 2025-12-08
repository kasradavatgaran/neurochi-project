

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
