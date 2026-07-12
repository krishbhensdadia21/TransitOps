"""
Trip Routes with Business Rules
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import math
import uuid

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.trip import Trip
from backend.app.schemas.trip import (
    TripCreate, 
    TripUpdate, 
    TripComplete,
    TripCancel,
    TripInDB, 
    TripListResponse,
    VehicleSummary,
    DriverSummary
)

router = APIRouter(prefix="/trips", tags=["Trips"])


def generate_trip_number():
    """Generate unique trip number"""
    prefix = "TRP"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(uuid.uuid4())[:4].upper()
    return f"{prefix}-{timestamp}-{random_suffix}"


def validate_vehicle_for_dispatch(vehicle: Vehicle, cargo_weight: Optional[Decimal] = None):
    """Validate vehicle can be dispatched"""
    if vehicle.status == "in_shop":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is in maintenance shop and cannot be dispatched"
        )
    
    if vehicle.status == "retired":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is retired and cannot be dispatched"
        )
    
    if vehicle.status == "on_trip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is already on another trip"
        )
    
    if cargo_weight and cargo_weight > vehicle.max_load_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cargo weight ({cargo_weight}kg) exceeds vehicle capacity ({vehicle.max_load_capacity}kg)"
        )


def validate_driver_for_dispatch(driver: Driver):
    """Validate driver can be dispatched"""
    if driver.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver is suspended and cannot be assigned"
        )
    
    if driver.status == "on_trip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver is already on another trip"
        )
    
    if driver.license_expiry < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver's license has expired"
        )


@router.get("", response_model=TripListResponse)
async def get_trips(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    driver_id: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("trips:view"))
):
    """Get paginated list of trips"""
    query = db.query(Trip).options(
        joinedload(Trip.vehicle),
        joinedload(Trip.driver)
    )
    
    if search:
        search_filter = or_(
            Trip.trip_number.ilike(f"%{search}%"),
            Trip.source.ilike(f"%{search}%"),
            Trip.destination.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if status and status != "all":
        query = query.filter(Trip.status == status)
    
    if vehicle_id:
        query = query.filter(Trip.vehicle_id == vehicle_id)
    
    if driver_id:
        query = query.filter(Trip.driver_id == driver_id)
    
    total = query.count()
    
    sort_column = getattr(Trip, sort_by, Trip.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    offset = (page - 1) * limit
    trips = query.offset(offset).limit(limit).all()
    
    return TripListResponse(
        trips=[TripInDB(
            id=str(t.id),
            trip_number=t.trip_number,
            source=t.source,
            destination=t.destination,
            vehicle_id=str(t.vehicle_id) if t.vehicle_id else None,
            driver_id=str(t.driver_id) if t.driver_id else None,
            cargo_description=t.cargo_description,
            cargo_weight=t.cargo_weight,
            planned_distance=t.planned_distance,
            actual_distance=t.actual_distance,
            fuel_used=t.fuel_used,
            scheduled_departure=t.scheduled_departure,
            actual_departure=t.actual_departure,
            scheduled_arrival=t.scheduled_arrival,
            actual_arrival=t.actual_arrival,
            status=t.status,
            notes=t.notes,
            dispatched_at=t.dispatched_at,
            completed_at=t.completed_at,
            cancelled_at=t.cancelled_at,
            cancellation_reason=t.cancellation_reason,
            created_at=t.created_at,
            updated_at=t.updated_at,
            vehicle=VehicleSummary(
                id=str(t.vehicle.id),
                registration_number=t.vehicle.registration_number,
                vehicle_name=t.vehicle.vehicle_name
            ) if t.vehicle else None,
            driver=DriverSummary(
                id=str(t.driver.id),
                first_name=t.driver.first_name,
                last_name=t.driver.last_name
            ) if t.driver else None
        ) for t in trips],
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1
    )


@router.post("", response_model=TripInDB, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("trips:create"))
):
    """Create a new trip (Draft status)"""
    vehicle = None
    driver = None
    
    # Validate vehicle if provided
    if trip.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == trip.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        validate_vehicle_for_dispatch(vehicle, trip.cargo_weight)
    
    # Validate driver if provided
    if trip.driver_id:
        driver = db.query(Driver).filter(Driver.id == trip.driver_id).first()
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        validate_driver_for_dispatch(driver)
    
    new_trip = Trip(
        trip_number=generate_trip_number(),
        source=trip.source,
        destination=trip.destination,
        vehicle_id=trip.vehicle_id,
        driver_id=trip.driver_id,
        cargo_description=trip.cargo_description,
        cargo_weight=trip.cargo_weight,
        planned_distance=trip.planned_distance,
        scheduled_departure=trip.scheduled_departure,
        scheduled_arrival=trip.scheduled_arrival,
        notes=trip.notes,
        status="draft",
        created_by=current_user.id
    )
    
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    
    return TripInDB(
        id=str(new_trip.id),
        trip_number=new_trip.trip_number,
        source=new_trip.source,
        destination=new_trip.destination,
        vehicle_id=str(new_trip.vehicle_id) if new_trip.vehicle_id else None,
        driver_id=str(new_trip.driver_id) if new_trip.driver_id else None,
        cargo_description=new_trip.cargo_description,
        cargo_weight=new_trip.cargo_weight,
        planned_distance=new_trip.planned_distance,
        actual_distance=new_trip.actual_distance,
        fuel_used=new_trip.fuel_used,
        scheduled_departure=new_trip.scheduled_departure,
        actual_departure=new_trip.actual_departure,
        scheduled_arrival=new_trip.scheduled_arrival,
        actual_arrival=new_trip.actual_arrival,
        status=new_trip.status,
        notes=new_trip.notes,
        dispatched_at=new_trip.dispatched_at,
        completed_at=new_trip.completed_at,
        cancelled_at=new_trip.cancelled_at,
        cancellation_reason=new_trip.cancellation_reason,
        created_at=new_trip.created_at,
        updated_at=new_trip.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        ) if vehicle else None,
        driver=DriverSummary(
            id=str(driver.id),
            first_name=driver.first_name,
            last_name=driver.last_name
        ) if driver else None
    )


@router.post("/{trip_id}/dispatch", response_model=TripInDB)
async def dispatch_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("trips:dispatch"))
):
    """
    Dispatch a trip - BUSINESS RULES:
    - Vehicle must be available (not in_shop, retired, or on_trip)
    - Driver must be available (not suspended, on_trip, or expired license)
    - Vehicle and Driver status change to 'on_trip'
    """
    trip = db.query(Trip).options(
        joinedload(Trip.vehicle),
        joinedload(Trip.driver)
    ).filter(Trip.id == trip_id).first()
    
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    
    if trip.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft trips can be dispatched")
    
    if not trip.vehicle_id or not trip.driver_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle and driver must be assigned before dispatch")
    
    vehicle = trip.vehicle
    driver = trip.driver
    
    # Validate business rules
    validate_vehicle_for_dispatch(vehicle, trip.cargo_weight)
    validate_driver_for_dispatch(driver)
    
    # Update statuses - BUSINESS RULE
    vehicle.status = "on_trip"
    driver.status = "on_trip"
    
    # Update trip
    trip.status = "dispatched"
    trip.dispatched_by = current_user.id
    trip.dispatched_at = datetime.utcnow()
    trip.actual_departure = datetime.utcnow()
    
    db.commit()
    db.refresh(trip)
    
    return TripInDB(
        id=str(trip.id),
        trip_number=trip.trip_number,
        source=trip.source,
        destination=trip.destination,
        vehicle_id=str(trip.vehicle_id),
        driver_id=str(trip.driver_id),
        cargo_description=trip.cargo_description,
        cargo_weight=trip.cargo_weight,
        planned_distance=trip.planned_distance,
        actual_distance=trip.actual_distance,
        fuel_used=trip.fuel_used,
        scheduled_departure=trip.scheduled_departure,
        actual_departure=trip.actual_departure,
        scheduled_arrival=trip.scheduled_arrival,
        actual_arrival=trip.actual_arrival,
        status=trip.status,
        notes=trip.notes,
        dispatched_at=trip.dispatched_at,
        completed_at=trip.completed_at,
        cancelled_at=trip.cancelled_at,
        cancellation_reason=trip.cancellation_reason,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        ),
        driver=DriverSummary(
            id=str(driver.id),
            first_name=driver.first_name,
            last_name=driver.last_name
        )
    )


@router.post("/{trip_id}/complete", response_model=TripInDB)
async def complete_trip(
    trip_id: str,
    complete_data: TripComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("trips:edit"))
):
    """
    Complete a trip - BUSINESS RULES:
    - Vehicle status changes to 'available'
    - Driver status changes to 'available'
    - Driver stats are updated
    """
    trip = db.query(Trip).options(
        joinedload(Trip.vehicle),
        joinedload(Trip.driver)
    ).filter(Trip.id == trip_id).first()
    
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    
    if trip.status != "dispatched":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only dispatched trips can be completed")
    
    vehicle = trip.vehicle
    driver = trip.driver
    
    # Update vehicle - BUSINESS RULE
    if vehicle:
        vehicle.status = "available"
        if complete_data.actual_distance:
            vehicle.odometer = Decimal(str(vehicle.odometer)) + complete_data.actual_distance
    
    # Update driver - BUSINESS RULE
    if driver:
        driver.status = "available"
        driver.total_trips += 1
        if complete_data.actual_distance:
            driver.total_distance = Decimal(str(driver.total_distance)) + complete_data.actual_distance
    
    # Update trip
    trip.status = "completed"
    trip.actual_distance = complete_data.actual_distance
    trip.fuel_used = complete_data.fuel_used
    trip.actual_arrival = datetime.utcnow()
    trip.completed_at = datetime.utcnow()
    if complete_data.notes:
        trip.notes = complete_data.notes
    
    db.commit()
    db.refresh(trip)
    
    return TripInDB(
        id=str(trip.id),
        trip_number=trip.trip_number,
        source=trip.source,
        destination=trip.destination,
        vehicle_id=str(trip.vehicle_id) if trip.vehicle_id else None,
        driver_id=str(trip.driver_id) if trip.driver_id else None,
        cargo_description=trip.cargo_description,
        cargo_weight=trip.cargo_weight,
        planned_distance=trip.planned_distance,
        actual_distance=trip.actual_distance,
        fuel_used=trip.fuel_used,
        scheduled_departure=trip.scheduled_departure,
        actual_departure=trip.actual_departure,
        scheduled_arrival=trip.scheduled_arrival,
        actual_arrival=trip.actual_arrival,
        status=trip.status,
        notes=trip.notes,
        dispatched_at=trip.dispatched_at,
        completed_at=trip.completed_at,
        cancelled_at=trip.cancelled_at,
        cancellation_reason=trip.cancellation_reason,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        ) if vehicle else None,
        driver=DriverSummary(
            id=str(driver.id),
            first_name=driver.first_name,
            last_name=driver.last_name
        ) if driver else None
    )


@router.post("/{trip_id}/cancel", response_model=TripInDB)
async def cancel_trip(
    trip_id: str,
    cancel_data: TripCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("trips:edit"))
):
    """
    Cancel a trip - BUSINESS RULES:
    - If dispatched, restore vehicle and driver to 'available'
    """
    trip = db.query(Trip).options(
        joinedload(Trip.vehicle),
        joinedload(Trip.driver)
    ).filter(Trip.id == trip_id).first()
    
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    
    if trip.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip is already completed or cancelled")
    
    # Restore availability if dispatched - BUSINESS RULE
    if trip.status == "dispatched":
        if trip.vehicle:
            trip.vehicle.status = "available"
        if trip.driver:
            trip.driver.status = "available"
    
    # Update trip
    trip.status = "cancelled"
    trip.cancelled_at = datetime.utcnow()
    trip.cancellation_reason = cancel_data.cancellation_reason
    
    db.commit()
    db.refresh(trip)
    
    vehicle = trip.vehicle
    driver = trip.driver
    
    return TripInDB(
        id=str(trip.id),
        trip_number=trip.trip_number,
        source=trip.source,
        destination=trip.destination,
        vehicle_id=str(trip.vehicle_id) if trip.vehicle_id else None,
        driver_id=str(trip.driver_id) if trip.driver_id else None,
        cargo_description=trip.cargo_description,
        cargo_weight=trip.cargo_weight,
        planned_distance=trip.planned_distance,
        actual_distance=trip.actual_distance,
        fuel_used=trip.fuel_used,
        scheduled_departure=trip.scheduled_departure,
        actual_departure=trip.actual_departure,
        scheduled_arrival=trip.scheduled_arrival,
        actual_arrival=trip.actual_arrival,
        status=trip.status,
        notes=trip.notes,
        dispatched_at=trip.dispatched_at,
        completed_at=trip.completed_at,
        cancelled_at=trip.cancelled_at,
        cancellation_reason=trip.cancellation_reason,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        ) if vehicle else None,
        driver=DriverSummary(
            id=str(driver.id),
            first_name=driver.first_name,
            last_name=driver.last_name
        ) if driver else None
    )


@router.put("/{trip_id}", response_model=TripInDB)
async def update_trip(
    trip_id: str,
    trip_update: TripUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("trips:edit"))
):
    """Update trip - only draft trips can be fully edited"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    
    if trip.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft trips can be edited")
    
    # Validate new vehicle if provided
    if trip_update.vehicle_id and trip_update.vehicle_id != str(trip.vehicle_id):
        vehicle = db.query(Vehicle).filter(Vehicle.id == trip_update.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
        cargo_weight = trip_update.cargo_weight or trip.cargo_weight
        validate_vehicle_for_dispatch(vehicle, cargo_weight)
    
    # Validate new driver if provided
    if trip_update.driver_id and trip_update.driver_id != str(trip.driver_id):
        driver = db.query(Driver).filter(Driver.id == trip_update.driver_id).first()
        if not driver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        validate_driver_for_dispatch(driver)
    
    update_data = trip_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)
    
    db.commit()
    db.refresh(trip)
    
    # Reload with relationships
    trip = db.query(Trip).options(
        joinedload(Trip.vehicle),
        joinedload(Trip.driver)
    ).filter(Trip.id == trip_id).first()
    
    return TripInDB(
        id=str(trip.id),
        trip_number=trip.trip_number,
        source=trip.source,
        destination=trip.destination,
        vehicle_id=str(trip.vehicle_id) if trip.vehicle_id else None,
        driver_id=str(trip.driver_id) if trip.driver_id else None,
        cargo_description=trip.cargo_description,
        cargo_weight=trip.cargo_weight,
        planned_distance=trip.planned_distance,
        actual_distance=trip.actual_distance,
        fuel_used=trip.fuel_used,
        scheduled_departure=trip.scheduled_departure,
        actual_departure=trip.actual_departure,
        scheduled_arrival=trip.scheduled_arrival,
        actual_arrival=trip.actual_arrival,
        status=trip.status,
        notes=trip.notes,
        dispatched_at=trip.dispatched_at,
        completed_at=trip.completed_at,
        cancelled_at=trip.cancelled_at,
        cancellation_reason=trip.cancellation_reason,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        vehicle=VehicleSummary(
            id=str(trip.vehicle.id),
            registration_number=trip.vehicle.registration_number,
            vehicle_name=trip.vehicle.vehicle_name
        ) if trip.vehicle else None,
        driver=DriverSummary(
            id=str(trip.driver.id),
            first_name=trip.driver.first_name,
            last_name=trip.driver.last_name
        ) if trip.driver else None
    )


@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("trips:delete"))
):
    """Delete trip - only draft trips can be deleted"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    
    if trip.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft trips can be deleted")
    
    db.delete(trip)
    db.commit()
    
    return {"message": "Trip deleted successfully"}
