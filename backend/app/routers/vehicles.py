"""
Vehicle Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
import math

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, require_permission
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle
from backend.app.models.trip import Trip
from backend.app.models.maintenance import Maintenance
from backend.app.schemas.vehicle import (
    VehicleCreate, 
    VehicleUpdate, 
    VehicleInDB, 
    VehicleListResponse
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=VehicleListResponse)
async def get_vehicles(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vehicles:view"))
):
    """Get paginated list of vehicles"""
    query = db.query(Vehicle)
    
    # Apply filters
    if search:
        search_filter = or_(
            Vehicle.registration_number.ilike(f"%{search}%"),
            Vehicle.vehicle_name.ilike(f"%{search}%"),
            Vehicle.vehicle_model.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if status and status != "all":
        query = query.filter(Vehicle.status == status)
    
    if vehicle_type and vehicle_type != "all":
        query = query.filter(Vehicle.vehicle_type == vehicle_type)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Vehicle, sort_by, Vehicle.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * limit
    vehicles = query.offset(offset).limit(limit).all()
    
    return VehicleListResponse(
        vehicles=[VehicleInDB(
            id=str(v.id),
            registration_number=v.registration_number,
            vehicle_name=v.vehicle_name,
            vehicle_model=v.vehicle_model,
            vehicle_type=v.vehicle_type,
            max_load_capacity=v.max_load_capacity,
            odometer=v.odometer,
            acquisition_cost=v.acquisition_cost,
            status=v.status,
            manufacturer=v.manufacturer,
            year=v.year,
            fuel_type=v.fuel_type,
            insurance_expiry=v.insurance_expiry,
            last_service_date=v.last_service_date,
            notes=v.notes,
            created_at=v.created_at,
            updated_at=v.updated_at
        ) for v in vehicles],
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1
    )


@router.post("", response_model=VehicleInDB, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vehicles:create"))
):
    """Create a new vehicle"""
    # Check for duplicate registration number
    existing = db.query(Vehicle).filter(
        Vehicle.registration_number == vehicle.registration_number.upper()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle with this registration number already exists"
        )
    
    new_vehicle = Vehicle(
        registration_number=vehicle.registration_number.upper(),
        vehicle_name=vehicle.vehicle_name,
        vehicle_model=vehicle.vehicle_model,
        vehicle_type=vehicle.vehicle_type,
        max_load_capacity=vehicle.max_load_capacity,
        odometer=vehicle.odometer or 0,
        acquisition_cost=vehicle.acquisition_cost,
        status="available",
        manufacturer=vehicle.manufacturer,
        year=vehicle.year,
        fuel_type=vehicle.fuel_type,
        insurance_expiry=vehicle.insurance_expiry,
        last_service_date=vehicle.last_service_date,
        notes=vehicle.notes
    )
    
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)
    
    return VehicleInDB(
        id=str(new_vehicle.id),
        registration_number=new_vehicle.registration_number,
        vehicle_name=new_vehicle.vehicle_name,
        vehicle_model=new_vehicle.vehicle_model,
        vehicle_type=new_vehicle.vehicle_type,
        max_load_capacity=new_vehicle.max_load_capacity,
        odometer=new_vehicle.odometer,
        acquisition_cost=new_vehicle.acquisition_cost,
        status=new_vehicle.status,
        manufacturer=new_vehicle.manufacturer,
        year=new_vehicle.year,
        fuel_type=new_vehicle.fuel_type,
        insurance_expiry=new_vehicle.insurance_expiry,
        last_service_date=new_vehicle.last_service_date,
        notes=new_vehicle.notes,
        created_at=new_vehicle.created_at,
        updated_at=new_vehicle.updated_at
    )


@router.get("/{vehicle_id}", response_model=VehicleInDB)
async def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vehicles:view"))
):
    """Get vehicle by ID"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    return VehicleInDB(
        id=str(vehicle.id),
        registration_number=vehicle.registration_number,
        vehicle_name=vehicle.vehicle_name,
        vehicle_model=vehicle.vehicle_model,
        vehicle_type=vehicle.vehicle_type,
        max_load_capacity=vehicle.max_load_capacity,
        odometer=vehicle.odometer,
        acquisition_cost=vehicle.acquisition_cost,
        status=vehicle.status,
        manufacturer=vehicle.manufacturer,
        year=vehicle.year,
        fuel_type=vehicle.fuel_type,
        insurance_expiry=vehicle.insurance_expiry,
        last_service_date=vehicle.last_service_date,
        notes=vehicle.notes,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at
    )


@router.put("/{vehicle_id}", response_model=VehicleInDB)
async def update_vehicle(
    vehicle_id: str,
    vehicle_update: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vehicles:edit"))
):
    """Update vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Check for duplicate registration if changing
    if vehicle_update.registration_number:
        existing = db.query(Vehicle).filter(
            Vehicle.registration_number == vehicle_update.registration_number.upper(),
            Vehicle.id != vehicle_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vehicle with this registration number already exists"
            )
    
    # Update fields
    update_data = vehicle_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "registration_number" and value:
            value = value.upper()
        setattr(vehicle, field, value)
    
    db.commit()
    db.refresh(vehicle)
    
    return VehicleInDB(
        id=str(vehicle.id),
        registration_number=vehicle.registration_number,
        vehicle_name=vehicle.vehicle_name,
        vehicle_model=vehicle.vehicle_model,
        vehicle_type=vehicle.vehicle_type,
        max_load_capacity=vehicle.max_load_capacity,
        odometer=vehicle.odometer,
        acquisition_cost=vehicle.acquisition_cost,
        status=vehicle.status,
        manufacturer=vehicle.manufacturer,
        year=vehicle.year,
        fuel_type=vehicle.fuel_type,
        insurance_expiry=vehicle.insurance_expiry,
        last_service_date=vehicle.last_service_date,
        notes=vehicle.notes,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at
    )


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("vehicles:delete"))
):
    """Delete vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found"
        )
    
    # Check for active trips
    active_trip = db.query(Trip).filter(
        Trip.vehicle_id == vehicle_id,
        Trip.status.in_(["draft", "dispatched"])
    ).first()
    
    if active_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete vehicle with active trips"
        )
    
    # Check for active maintenance
    active_maintenance = db.query(Maintenance).filter(
        Maintenance.vehicle_id == vehicle_id,
        Maintenance.status.in_(["scheduled", "in_progress"])
    ).first()
    
    if active_maintenance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete vehicle with active maintenance"
        )
    
    db.delete(vehicle)
    db.commit()
    
    return {"message": "Vehicle deleted successfully"}
