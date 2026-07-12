"""
Driver Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import date
import math

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.models.user import User
from backend.app.models.driver import Driver
from backend.app.models.trip import Trip
from backend.app.schemas.driver import (
    DriverCreate, 
    DriverUpdate, 
    DriverInDB, 
    DriverListResponse
)

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=DriverListResponse)
async def get_drivers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("drivers:view"))
):
    """Get paginated list of drivers"""
    query = db.query(Driver)
    
    if search:
        search_filter = or_(
            Driver.first_name.ilike(f"%{search}%"),
            Driver.last_name.ilike(f"%{search}%"),
            Driver.license_number.ilike(f"%{search}%"),
            Driver.contact_number.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if status and status != "all":
        query = query.filter(Driver.status == status)
    
    total = query.count()
    
    sort_column = getattr(Driver, sort_by, Driver.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    offset = (page - 1) * limit
    drivers = query.offset(offset).limit(limit).all()
    
    return DriverListResponse(
        drivers=[DriverInDB(
            id=str(d.id),
            first_name=d.first_name,
            last_name=d.last_name,
            license_number=d.license_number,
            license_category=d.license_category,
            license_expiry=d.license_expiry,
            contact_number=d.contact_number,
            email=d.email,
            address=d.address,
            emergency_contact=d.emergency_contact,
            safety_score=d.safety_score,
            total_trips=d.total_trips,
            total_distance=d.total_distance,
            status=d.status,
            date_of_birth=d.date_of_birth,
            hire_date=d.hire_date,
            notes=d.notes,
            created_at=d.created_at,
            updated_at=d.updated_at
        ) for d in drivers],
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1
    )


@router.post("", response_model=DriverInDB, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver: DriverCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("drivers:create"))
):
    """Create a new driver"""
    existing = db.query(Driver).filter(
        Driver.license_number == driver.license_number.upper()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver with this license number already exists"
        )
    
    new_driver = Driver(
        first_name=driver.first_name,
        last_name=driver.last_name,
        license_number=driver.license_number.upper(),
        license_category=driver.license_category,
        license_expiry=driver.license_expiry,
        contact_number=driver.contact_number,
        email=driver.email,
        address=driver.address,
        emergency_contact=driver.emergency_contact,
        date_of_birth=driver.date_of_birth,
        hire_date=driver.hire_date,
        notes=driver.notes,
        status="available",
        safety_score=100
    )
    
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    
    return DriverInDB(
        id=str(new_driver.id),
        first_name=new_driver.first_name,
        last_name=new_driver.last_name,
        license_number=new_driver.license_number,
        license_category=new_driver.license_category,
        license_expiry=new_driver.license_expiry,
        contact_number=new_driver.contact_number,
        email=new_driver.email,
        address=new_driver.address,
        emergency_contact=new_driver.emergency_contact,
        safety_score=new_driver.safety_score,
        total_trips=new_driver.total_trips,
        total_distance=new_driver.total_distance,
        status=new_driver.status,
        date_of_birth=new_driver.date_of_birth,
        hire_date=new_driver.hire_date,
        notes=new_driver.notes,
        created_at=new_driver.created_at,
        updated_at=new_driver.updated_at
    )


@router.get("/{driver_id}", response_model=DriverInDB)
async def get_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("drivers:view"))
):
    """Get driver by ID"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    return DriverInDB(
        id=str(driver.id),
        first_name=driver.first_name,
        last_name=driver.last_name,
        license_number=driver.license_number,
        license_category=driver.license_category,
        license_expiry=driver.license_expiry,
        contact_number=driver.contact_number,
        email=driver.email,
        address=driver.address,
        emergency_contact=driver.emergency_contact,
        safety_score=driver.safety_score,
        total_trips=driver.total_trips,
        total_distance=driver.total_distance,
        status=driver.status,
        date_of_birth=driver.date_of_birth,
        hire_date=driver.hire_date,
        notes=driver.notes,
        created_at=driver.created_at,
        updated_at=driver.updated_at
    )


@router.put("/{driver_id}", response_model=DriverInDB)
async def update_driver(
    driver_id: str,
    driver_update: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("drivers:edit"))
):
    """Update driver"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    if driver_update.license_number:
        existing = db.query(Driver).filter(
            Driver.license_number == driver_update.license_number.upper(),
            Driver.id != driver_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Driver with this license number already exists"
            )
    
    update_data = driver_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "license_number" and value:
            value = value.upper()
        setattr(driver, field, value)
    
    db.commit()
    db.refresh(driver)
    
    return DriverInDB(
        id=str(driver.id),
        first_name=driver.first_name,
        last_name=driver.last_name,
        license_number=driver.license_number,
        license_category=driver.license_category,
        license_expiry=driver.license_expiry,
        contact_number=driver.contact_number,
        email=driver.email,
        address=driver.address,
        emergency_contact=driver.emergency_contact,
        safety_score=driver.safety_score,
        total_trips=driver.total_trips,
        total_distance=driver.total_distance,
        status=driver.status,
        date_of_birth=driver.date_of_birth,
        hire_date=driver.hire_date,
        notes=driver.notes,
        created_at=driver.created_at,
        updated_at=driver.updated_at
    )


@router.delete("/{driver_id}")
async def delete_driver(
    driver_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("drivers:delete"))
):
    """Delete driver"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    active_trip = db.query(Trip).filter(
        Trip.driver_id == driver_id,
        Trip.status.in_(["draft", "dispatched"])
    ).first()
    
    if active_trip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete driver with active trips"
        )
    
    db.delete(driver)
    db.commit()
    
    return {"message": "Driver deleted successfully"}
