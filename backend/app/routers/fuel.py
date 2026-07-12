"""
Fuel Log Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from decimal import Decimal
import math

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle
from backend.app.models.fuel import FuelLog
from backend.app.models.expense import Expense
from backend.app.schemas.fuel import (
    FuelLogCreate, 
    FuelLogUpdate, 
    FuelLogInDB, 
    FuelLogListResponse,
    VehicleSummary,
    TripSummary
)

router = APIRouter(prefix="/fuel", tags=["Fuel Logs"])


@router.get("", response_model=FuelLogListResponse)
async def get_fuel_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    vehicle_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "fuel_date",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fuel:view"))
):
    """Get paginated list of fuel logs"""
    query = db.query(FuelLog).options(
        joinedload(FuelLog.vehicle),
        joinedload(FuelLog.trip)
    )
    
    if vehicle_id:
        query = query.filter(FuelLog.vehicle_id == vehicle_id)
    
    if start_date:
        query = query.filter(FuelLog.fuel_date >= start_date)
    
    if end_date:
        query = query.filter(FuelLog.fuel_date <= end_date)
    
    total = query.count()
    
    sort_column = getattr(FuelLog, sort_by, FuelLog.fuel_date)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    offset = (page - 1) * limit
    logs = query.offset(offset).limit(limit).all()
    
    return FuelLogListResponse(
        fuel_logs=[FuelLogInDB(
            id=str(f.id),
            vehicle_id=str(f.vehicle_id),
            trip_id=str(f.trip_id) if f.trip_id else None,
            fuel_quantity=f.fuel_quantity,
            fuel_cost=f.fuel_cost,
            price_per_unit=f.price_per_unit,
            fuel_type=f.fuel_type,
            odometer_reading=f.odometer_reading,
            fuel_station=f.fuel_station,
            location=f.location,
            fuel_date=f.fuel_date,
            receipt_number=f.receipt_number,
            notes=f.notes,
            created_at=f.created_at,
            updated_at=f.updated_at,
            vehicle=VehicleSummary(
                id=str(f.vehicle.id),
                registration_number=f.vehicle.registration_number,
                vehicle_name=f.vehicle.vehicle_name
            ) if f.vehicle else None,
            trip=TripSummary(
                id=str(f.trip.id),
                trip_number=f.trip.trip_number
            ) if f.trip else None
        ) for f in logs],
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1
    )


@router.post("", response_model=FuelLogInDB, status_code=status.HTTP_201_CREATED)
async def create_fuel_log(
    fuel_log: FuelLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fuel:create"))
):
    """Create a new fuel log - automatically creates expense record"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == fuel_log.vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    # Calculate price per unit
    price_per_unit = fuel_log.fuel_cost / fuel_log.fuel_quantity
    
    new_log = FuelLog(
        vehicle_id=fuel_log.vehicle_id,
        trip_id=fuel_log.trip_id,
        fuel_quantity=fuel_log.fuel_quantity,
        fuel_cost=fuel_log.fuel_cost,
        price_per_unit=price_per_unit,
        fuel_type=fuel_log.fuel_type,
        odometer_reading=fuel_log.odometer_reading,
        fuel_station=fuel_log.fuel_station,
        location=fuel_log.location,
        fuel_date=fuel_log.fuel_date,
        receipt_number=fuel_log.receipt_number,
        notes=fuel_log.notes,
        created_by=current_user.id
    )
    
    # Update vehicle odometer if provided
    if fuel_log.odometer_reading:
        vehicle.odometer = fuel_log.odometer_reading
    
    # Create expense record
    expense = Expense(
        vehicle_id=fuel_log.vehicle_id,
        trip_id=fuel_log.trip_id,
        expense_type="fuel",
        description=f"Fuel - {fuel_log.fuel_quantity}L at {fuel_log.fuel_station or 'Unknown Station'}",
        amount=fuel_log.fuel_cost,
        expense_date=fuel_log.fuel_date,
        vendor=fuel_log.fuel_station,
        invoice_number=fuel_log.receipt_number,
        created_by=current_user.id
    )
    
    db.add(new_log)
    db.add(expense)
    db.commit()
    db.refresh(new_log)
    
    return FuelLogInDB(
        id=str(new_log.id),
        vehicle_id=str(new_log.vehicle_id),
        trip_id=str(new_log.trip_id) if new_log.trip_id else None,
        fuel_quantity=new_log.fuel_quantity,
        fuel_cost=new_log.fuel_cost,
        price_per_unit=new_log.price_per_unit,
        fuel_type=new_log.fuel_type,
        odometer_reading=new_log.odometer_reading,
        fuel_station=new_log.fuel_station,
        location=new_log.location,
        fuel_date=new_log.fuel_date,
        receipt_number=new_log.receipt_number,
        notes=new_log.notes,
        created_at=new_log.created_at,
        updated_at=new_log.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        ),
        trip=None
    )


@router.delete("/{fuel_log_id}")
async def delete_fuel_log(
    fuel_log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fuel:delete"))
):
    """Delete fuel log"""
    log = db.query(FuelLog).filter(FuelLog.id == fuel_log_id).first()
    
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fuel log not found")
    
    db.delete(log)
    db.commit()
    
    return {"message": "Fuel log deleted successfully"}
