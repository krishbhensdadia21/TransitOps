"""
Vehicle Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class VehicleBase(BaseModel):
    registration_number: str = Field(..., min_length=1, max_length=50)
    vehicle_name: str = Field(..., min_length=1, max_length=100)
    vehicle_model: str = Field(..., min_length=1, max_length=100)
    vehicle_type: str = Field(..., pattern="^(truck|van|bus|trailer|tanker|pickup)$")
    max_load_capacity: Decimal = Field(..., gt=0)
    acquisition_cost: Decimal = Field(..., gt=0)
    odometer: Optional[Decimal] = 0
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    insurance_expiry: Optional[date] = None
    last_service_date: Optional[date] = None
    notes: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    registration_number: Optional[str] = None
    vehicle_name: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_type: Optional[str] = None
    max_load_capacity: Optional[Decimal] = None
    acquisition_cost: Optional[Decimal] = None
    odometer: Optional[Decimal] = None
    status: Optional[str] = None
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    insurance_expiry: Optional[date] = None
    last_service_date: Optional[date] = None
    notes: Optional[str] = None


class VehicleInDB(BaseModel):
    id: str
    registration_number: str
    vehicle_name: str
    vehicle_model: str
    vehicle_type: str
    max_load_capacity: Decimal
    odometer: Decimal
    acquisition_cost: Decimal
    status: str
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    fuel_type: Optional[str] = None
    insurance_expiry: Optional[date] = None
    last_service_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    vehicles: List[VehicleInDB]
    total: int
    page: int
    limit: int
    total_pages: int
