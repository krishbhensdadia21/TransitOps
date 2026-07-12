"""
Expense Schemas
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


class ExpenseBase(BaseModel):
    vehicle_id: Optional[str] = None
    trip_id: Optional[str] = None
    expense_type: str = Field(..., pattern="^(fuel|maintenance|toll|insurance|registration|salary|other)$")
    description: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    expense_date: date
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    is_recurring: Optional[bool] = False
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    vehicle_id: Optional[str] = None
    trip_id: Optional[str] = None
    expense_type: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    is_recurring: Optional[bool] = None
    notes: Optional[str] = None


class ExpenseInDB(BaseModel):
    id: str
    vehicle_id: Optional[str] = None
    trip_id: Optional[str] = None
    expense_type: str
    description: str
    amount: Decimal
    expense_date: date
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    is_recurring: bool
    notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    vehicle: Optional[VehicleSummary] = None
    trip: Optional[TripSummary] = None

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseInDB]
    total: int
    page: int
    limit: int
    total_pages: int
    total_amount: Decimal
