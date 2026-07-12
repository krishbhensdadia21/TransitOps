"""
Fuel Log Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class VehicleSummary(BaseModel):
    id: str
    registration_number: str
    vehicle_name: str

    class Config:
        from_attributes = True


class TripSummary(BaseModel):
    id: str
    trip_number: str

    class Config:
        from_attributes = True


class FuelLogBase(BaseModel):
    vehicle_id: str
    trip_id: Optional[str] = None
    fuel_quantity: Decimal = Field(..., gt=0)
    fuel_cost: Decimal = Field(..., gt=0)
    fuel_type: str = Field(..., min_length=1)
    fuel_date: date
    odometer_reading: Optional[Decimal] = None
    fuel_station: Optional[str] = None
    location: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class FuelLogCreate(FuelLogBase):
    pass


class FuelLogUpdate(BaseModel):
    fuel_quantity: Optional[Decimal] = None
    fuel_cost: Optional[Decimal] = None
    fuel_type: Optional[str] = None
    fuel_date: Optional[date] = None
    odometer_reading: Optional[Decimal] = None
    fuel_station: Optional[str] = None
    location: Optional[str] = None
    receipt_number: Optional[str] = None
    notes: Optional[str] = None


class FuelLogInDB(BaseModel):
    id: str
    vehicle_id: str
    trip_id: Optional[str] = None
    fuel_quantity: Decimal
    fuel_cost: Decimal
    price_per_unit: Optional[Decimal] = None
    fuel_type: str
    odometer_reading: Optional[Decimal] = None
    fuel_station: Optional[str] = None
    location: Optional[str] = None
    fuel_date: date
    receipt_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    vehicle: Optional[VehicleSummary] = None
    trip: Optional[TripSummary] = None

    class Config:
        from_attributes = True


class FuelLogListResponse(BaseModel):
    fuel_logs: List[FuelLogInDB]
    total: int
    page: int
    limit: int
    total_pages: int
