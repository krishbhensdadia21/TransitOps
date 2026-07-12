"""
Driver Schemas
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class DriverBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    license_number: str = Field(..., min_length=1, max_length=50)
    license_category: str = Field(..., pattern="^(A|B|C|D|E|CDL_A|CDL_B|CDL_C)$")
    license_expiry: date
    contact_number: str = Field(..., min_length=1, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    date_of_birth: Optional[date] = None
    hire_date: Optional[date] = None
    notes: Optional[str] = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    license_number: Optional[str] = None
    license_category: Optional[str] = None
    license_expiry: Optional[date] = None
    contact_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    safety_score: Optional[int] = None
    status: Optional[str] = None
    date_of_birth: Optional[date] = None
    hire_date: Optional[date] = None
    notes: Optional[str] = None


class DriverInDB(BaseModel):
    id: str
    first_name: str
    last_name: str
    license_number: str
    license_category: str
    license_expiry: date
    contact_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    safety_score: int
    total_trips: int
    total_distance: Decimal
    status: str
    date_of_birth: Optional[date] = None
    hire_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DriverListResponse(BaseModel):
    drivers: List[DriverInDB]
    total: int
    page: int
    limit: int
    total_pages: int
