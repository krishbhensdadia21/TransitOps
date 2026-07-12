"""
Expense Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import Optional
from decimal import Decimal
import math

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle
from backend.app.models.expense import Expense
from backend.app.schemas.expense import (
    ExpenseCreate, 
    ExpenseUpdate, 
    ExpenseInDB, 
    ExpenseListResponse,
    VehicleSummary,
    TripSummary
)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("", response_model=ExpenseListResponse)
async def get_expenses(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    expense_type: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "expense_date",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("expenses:view"))
):
    """Get paginated list of expenses"""
    query = db.query(Expense).options(
        joinedload(Expense.vehicle),
        joinedload(Expense.trip)
    )
    
    if search:
        search_filter = or_(
            Expense.description.ilike(f"%{search}%"),
            Expense.vendor.ilike(f"%{search}%"),
            Expense.invoice_number.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if expense_type and expense_type != "all":
        query = query.filter(Expense.expense_type == expense_type)
    
    if vehicle_id:
        query = query.filter(Expense.vehicle_id == vehicle_id)
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    # Get total count and amount
    total = query.count()
    total_amount = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.id.in_([e.id for e in query.all()])
    ).scalar() if total > 0 else Decimal("0")
    
    # Re-run query for pagination
    query = db.query(Expense).options(
        joinedload(Expense.vehicle),
        joinedload(Expense.trip)
    )
    
    if search:
        query = query.filter(or_(
            Expense.description.ilike(f"%{search}%"),
            Expense.vendor.ilike(f"%{search}%"),
            Expense.invoice_number.ilike(f"%{search}%")
        ))
    
    if expense_type and expense_type != "all":
        query = query.filter(Expense.expense_type == expense_type)
    
    if vehicle_id:
        query = query.filter(Expense.vehicle_id == vehicle_id)
    
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)
    
    sort_column = getattr(Expense, sort_by, Expense.expense_date)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    offset = (page - 1) * limit
    expenses = query.offset(offset).limit(limit).all()
    
    return ExpenseListResponse(
        expenses=[ExpenseInDB(
            id=str(e.id),
            vehicle_id=str(e.vehicle_id) if e.vehicle_id else None,
            trip_id=str(e.trip_id) if e.trip_id else None,
            expense_type=e.expense_type,
            description=e.description,
            amount=e.amount,
            expense_date=e.expense_date,
            vendor=e.vendor,
            invoice_number=e.invoice_number,
            is_recurring=e.is_recurring,
            notes=e.notes,
            approved_at=e.approved_at,
            created_at=e.created_at,
            updated_at=e.updated_at,
            vehicle=VehicleSummary(
                id=str(e.vehicle.id),
                registration_number=e.vehicle.registration_number,
                vehicle_name=e.vehicle.vehicle_name
            ) if e.vehicle else None,
            trip=TripSummary(
                id=str(e.trip.id),
                trip_number=e.trip.trip_number
            ) if e.trip else None
        ) for e in expenses],
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 1,
        total_amount=total_amount
    )


@router.post("", response_model=ExpenseInDB, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("expenses:create"))
):
    """Create a new expense"""
    if expense.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == expense.vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    
    new_expense = Expense(
        vehicle_id=expense.vehicle_id,
        trip_id=expense.trip_id,
        expense_type=expense.expense_type,
        description=expense.description,
        amount=expense.amount,
        expense_date=expense.expense_date,
        vendor=expense.vendor,
        invoice_number=expense.invoice_number,
        is_recurring=expense.is_recurring or False,
        notes=expense.notes,
        created_by=current_user.id
    )
    
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    return ExpenseInDB(
        id=str(new_expense.id),
        vehicle_id=str(new_expense.vehicle_id) if new_expense.vehicle_id else None,
        trip_id=str(new_expense.trip_id) if new_expense.trip_id else None,
        expense_type=new_expense.expense_type,
        description=new_expense.description,
        amount=new_expense.amount,
        expense_date=new_expense.expense_date,
        vendor=new_expense.vendor,
        invoice_number=new_expense.invoice_number,
        is_recurring=new_expense.is_recurring,
        notes=new_expense.notes,
        approved_at=new_expense.approved_at,
        created_at=new_expense.created_at,
        updated_at=new_expense.updated_at,
        vehicle=None,
        trip=None
    )


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("expenses:delete"))
):
    """Delete expense"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    
    return {"message": "Expense deleted successfully"}
