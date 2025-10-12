from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum
import uuid

Base = declarative_base()

class State(str, enum.Enum):
    exercise = "exercise"
    rest = "rest"
    daily = "daily"

class Status(str, enum.Enum):
    processing = "processing"
    waiting_user = "waiting_user"
    done = "done"
    error = "error"

class MeasurementDB(Base):
    __tablename__ = "measurements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SQLEnum(Status), default=Status.processing)
    state = Column(SQLEnum(State), nullable=True)
    fs = Column(Integer, nullable=False)
    format = Column(String(20), nullable=True)
    duration_sec = Column(Float, nullable=True)
    ecg_file_url = Column(String(500), nullable=True)
    results = Column(Text, nullable=True)  # JSON string
    errors = Column(Text, nullable=True)   # JSON string
    user_id = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    llm_answer = Column(Text, nullable=True)

# Pydantic models for API
class Measurement(BaseModel):
    id: str
    status: Status
    state: Optional[State] = None
    fs: int = Field(..., ge=50, le=2000)
    format: Optional[str] = None
    duration_sec: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    results: Optional[Dict[str, float]] = None
    errors: Optional[List[str]] = None
    llm_answer: Optional[str] = None

    class Config:
        orm_mode = True
        use_enum_values = True

class MeasurementCreate(BaseModel):
    fs: int = Field(..., ge=50, le=2000)
    state: State
    meta: Optional[str] = None

class MeasurementUpdate(BaseModel):
    state: Optional[State] = None

class CreateMeasurementFromJsonRequest(BaseModel):
    ecg: List[float] = Field(..., min_items=10)
    fs: int = Field(..., ge=50, le=2000)
    state: State

class MeasurementList(BaseModel):
    measurements: List[Measurement]
    total: int
    limit: int
    offset: int

class WebSocketMessage(BaseModel):
    type: str
    measurement_id: str
    status: Optional[Status] = None
    state: Optional[State] = None
    results: Optional[Dict[str, float]] = None
    errors: Optional[List[str]] = None
