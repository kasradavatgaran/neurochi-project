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



