"""
Maintenance Routes with Business Rules
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import math

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle
from backend.app.models.maintenance import Maintenance
from backend.app.models.expense import Expense
from backend.app.schemas.maintenance import (
    MaintenanceCreate, 
    MaintenanceUpdate, 
    MaintenanceComplete,
    MaintenanceInDB, 
    MaintenanceListResponse,
    VehicleSummary
)

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.get("", response_model=MaintenanceListResponse)
async def get_maintenance(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    vehicle_id: Optional[str] = None,
    maintenance_type: Optional[str] = None,
    sort_by: str = "scheduled_date",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maintenance:view"))
):
    """Get paginated list of maintenance records"""
    query = db.query(Maintenance).options(joinedload(Maintenance.vehicle))
    
    if search:
        search_filter = or_(
            Maintenance.description.ilike(f"%{search}%"),
            Maintenance.service_provider.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if status_filter and status_filter != "all":
        query = query.filter(Maintenance.status == status_filter)
    
    if vehicle_id:
        query = query.filter(Maintenance.vehicle_id == vehicle_id)
    
    if maintenance_type and maintenance_type != "all":
        query = query.filter(Maintenance.maintenance_type == maintenance_type)
    
    total = query.count()
    
    sort_column = getattr(Maintenance, sort_by, Maintenance.scheduled_date)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    offset = (page - 1) * limit
    records = query.offset(offset).limit(limit).all()
    
    return MaintenanceListResponse(
        maintenance=[MaintenanceInDB(
            id=str(m.id),
            vehicle_id=str(m.vehicle_id),
            maintenance_type=m.maintenance_type,
            description=m.description,
            scheduled_date=m.scheduled_date,
            start_date=m.start_date,
            completion_date=m.completion_date,
            estimated_cost=m.estimated_cost,
            actual_cost=m.actual_cost,
            odometer_at_service=m.odometer_at_service,
            service_provider=m.service_provider,
            invoice_number=m.invoice_number,
            status=m.status,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
            vehicle=VehicleSummary(
                id=str(m.vehicle.id),
                registration_number=m.vehicle.registration_number,
                vehicle_name=m.vehicle.vehicle_name
            ) if m.vehicle else None
        ) for m in records],
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1
    )


@router.post("", response_model=MaintenanceInDB, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    maintenance: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maintenance:create"))
):
    """
    Create maintenance record - BUSINESS RULES:
    - If start_immediately=True, vehicle status changes to 'in_shop'
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == maintenance.vehicle_id).first()
    
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    if vehicle.status == "on_trip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule maintenance for vehicle currently on trip"
        )
    
    new_status = "in_progress" if maintenance.start_immediately else "scheduled"
    
    # BUSINESS RULE: If starting immediately, change vehicle to in_shop
    if maintenance.start_immediately:
        vehicle.status = "in_shop"
    
    new_maintenance = Maintenance(
        vehicle_id=maintenance.vehicle_id,
        maintenance_type=maintenance.maintenance_type,
        description=maintenance.description,
        scheduled_date=maintenance.scheduled_date,
        start_date=maintenance.scheduled_date if maintenance.start_immediately else None,
        estimated_cost=maintenance.estimated_cost,
        odometer_at_service=vehicle.odometer,
        service_provider=maintenance.service_provider,
        notes=maintenance.notes,
        status=new_status,
        created_by=current_user.id
    )
    
    db.add(new_maintenance)
    db.commit()
    db.refresh(new_maintenance)
    
    return MaintenanceInDB(
        id=str(new_maintenance.id),
        vehicle_id=str(new_maintenance.vehicle_id),
        maintenance_type=new_maintenance.maintenance_type,
        description=new_maintenance.description,
        scheduled_date=new_maintenance.scheduled_date,
        start_date=new_maintenance.start_date,
        completion_date=new_maintenance.completion_date,
        estimated_cost=new_maintenance.estimated_cost,
        actual_cost=new_maintenance.actual_cost,
        odometer_at_service=new_maintenance.odometer_at_service,
        service_provider=new_maintenance.service_provider,
        invoice_number=new_maintenance.invoice_number,
        status=new_maintenance.status,
        notes=new_maintenance.notes,
        created_at=new_maintenance.created_at,
        updated_at=new_maintenance.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        )
    )


@router.post("/{maintenance_id}/start", response_model=MaintenanceInDB)
async def start_maintenance(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maintenance:edit"))
):
    """
    Start maintenance - BUSINESS RULE:
    - Vehicle status changes to 'in_shop'
    """
    record = db.query(Maintenance).options(
        joinedload(Maintenance.vehicle)
    ).filter(Maintenance.id == maintenance_id).first()
    
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    
    if record.status != "scheduled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only scheduled maintenance can be started")
    
    vehicle = record.vehicle
    
    if vehicle.status == "on_trip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start maintenance while vehicle is on trip"
        )
    
    # BUSINESS RULE: Vehicle becomes in_shop
    vehicle.status = "in_shop"
    
    record.status = "in_progress"
    record.start_date = date.today()
    record.odometer_at_service = vehicle.odometer
    
    db.commit()
    db.refresh(record)
    
    return MaintenanceInDB(
        id=str(record.id),
        vehicle_id=str(record.vehicle_id),
        maintenance_type=record.maintenance_type,
        description=record.description,
        scheduled_date=record.scheduled_date,
        start_date=record.start_date,
        completion_date=record.completion_date,
        estimated_cost=record.estimated_cost,
        actual_cost=record.actual_cost,
        odometer_at_service=record.odometer_at_service,
        service_provider=record.service_provider,
        invoice_number=record.invoice_number,
        status=record.status,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        )
    )


@router.post("/{maintenance_id}/complete", response_model=MaintenanceInDB)
async def complete_maintenance(
    maintenance_id: str,
    complete_data: MaintenanceComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maintenance:edit"))
):
    """
    Complete maintenance - BUSINESS RULES:
    - Vehicle status changes to 'available' (unless retired)
    - Creates expense record if cost provided
    """
    record = db.query(Maintenance).options(
        joinedload(Maintenance.vehicle)
    ).filter(Maintenance.id == maintenance_id).first()
    
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    
    if record.status != "in_progress":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only in-progress maintenance can be completed")
    
    vehicle = record.vehicle
    
    # BUSINESS RULE: Vehicle becomes available (unless retired)
    if vehicle.status != "retired":
        vehicle.status = "available"
    
    vehicle.last_service_date = date.today()
    
    record.status = "completed"
    record.completion_date = date.today()
    record.actual_cost = complete_data.actual_cost
    record.invoice_number = complete_data.invoice_number
    if complete_data.notes:
        record.notes = complete_data.notes
    
    # Create expense record if cost provided
    if complete_data.actual_cost and complete_data.actual_cost > 0:
        expense = Expense(
            vehicle_id=record.vehicle_id,
            expense_type="maintenance",
            description=f"Maintenance: {record.description}",
            amount=complete_data.actual_cost,
            expense_date=date.today(),
            vendor=record.service_provider,
            invoice_number=complete_data.invoice_number,
            created_by=current_user.id
        )
        db.add(expense)
    
    db.commit()
    db.refresh(record)
    
    return MaintenanceInDB(
        id=str(record.id),
        vehicle_id=str(record.vehicle_id),
        maintenance_type=record.maintenance_type,
        description=record.description,
        scheduled_date=record.scheduled_date,
        start_date=record.start_date,
        completion_date=record.completion_date,
        estimated_cost=record.estimated_cost,
        actual_cost=record.actual_cost,
        odometer_at_service=record.odometer_at_service,
        service_provider=record.service_provider,
        invoice_number=record.invoice_number,
        status=record.status,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
        vehicle=VehicleSummary(
            id=str(vehicle.id),
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name
        )
    )


@router.delete("/{maintenance_id}")
async def delete_maintenance(
    maintenance_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maintenance:delete"))
):
    """Delete maintenance record - only scheduled records can be deleted"""
    record = db.query(Maintenance).filter(Maintenance.id == maintenance_id).first()
    
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    
    if record.status == "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete in-progress maintenance"
        )
    
    db.delete(record)
    db.commit()
    
    return {"message": "Maintenance record deleted successfully"}
