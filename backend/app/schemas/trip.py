"""
Trip Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class VehicleSummary(BaseModel):
    id: str
    registration_number: str
    vehicle_name: str

    class Config:
        from_attributes = True


class DriverSummary(BaseModel):
    id: str
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class TripBase(BaseModel):
    source: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    cargo_description: Optional[str] = None
    cargo_weight: Optional[Decimal] = None
    planned_distance: Optional[Decimal] = None
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    notes: Optional[str] = None


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    source: Optional[str] = None
    destination: Optional[str] = None
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    cargo_description: Optional[str] = None
    cargo_weight: Optional[Decimal] = None
    planned_distance: Optional[Decimal] = None
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    notes: Optional[str] = None


class TripComplete(BaseModel):
    actual_distance: Optional[Decimal] = None
    fuel_used: Optional[Decimal] = None
    notes: Optional[str] = None


class TripCancel(BaseModel):
    cancellation_reason: str = Field(..., min_length=1)


class TripInDB(BaseModel):
    id: str
    trip_number: str
    source: str
    destination: str
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    cargo_description: Optional[str] = None
    cargo_weight: Optional[Decimal] = None
    planned_distance: Optional[Decimal] = None
    actual_distance: Optional[Decimal] = None
    fuel_used: Optional[Decimal] = None
    scheduled_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    vehicle: Optional[VehicleSummary] = None
    driver: Optional[DriverSummary] = None

    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    trips: List[TripInDB]
    total: int
    page: int
    limit: int
    total_pages: int
