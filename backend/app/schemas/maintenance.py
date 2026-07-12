"""
Maintenance Schemas
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


class MaintenanceBase(BaseModel):
    vehicle_id: str
    maintenance_type: str = Field(..., pattern="^(preventive|corrective|emergency|inspection)$")
    description: str = Field(..., min_length=1)
    scheduled_date: date
    estimated_cost: Optional[Decimal] = None
    service_provider: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceCreate(MaintenanceBase):
    start_immediately: Optional[bool] = False


class MaintenanceUpdate(BaseModel):
    maintenance_type: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[date] = None
    estimated_cost: Optional[Decimal] = None
    service_provider: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceComplete(BaseModel):
    actual_cost: Optional[Decimal] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceInDB(BaseModel):
    id: str
    vehicle_id: str
    maintenance_type: str
    description: str
    scheduled_date: date
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    odometer_at_service: Optional[Decimal] = None
    service_provider: Optional[str] = None
    invoice_number: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    vehicle: Optional[VehicleSummary] = None

    class Config:
        from_attributes = True


class MaintenanceListResponse(BaseModel):
    maintenance: List[MaintenanceInDB]
    total: int
    page: int
    limit: int
    total_pages: int
