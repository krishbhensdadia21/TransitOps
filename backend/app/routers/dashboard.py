"""
Dashboard & Analytics Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from backend.app.core.database import get_db
from backend.app.core.dependencies import require_permission
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.trip import Trip
from backend.app.models.maintenance import Maintenance
from backend.app.models.fuel import FuelLog
from backend.app.models.expense import Expense
from backend.app.core.security import hash_password

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("dashboard:view"))
):
    """Get dashboard KPIs and statistics"""
    
    # Current month date range
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    
    # Vehicle statistics
    vehicle_stats = db.query(
        func.count(Vehicle.id).label('total'),
        func.sum(case((Vehicle.status == 'available', 1), else_=0)).label('available'),
        func.sum(case((Vehicle.status == 'on_trip', 1), else_=0)).label('on_trip'),
        func.sum(case((Vehicle.status == 'in_shop', 1), else_=0)).label('in_shop'),
        func.sum(case((Vehicle.status == 'retired', 1), else_=0)).label('retired')
    ).first()
    
    # Driver statistics
    driver_stats = db.query(
        func.count(Driver.id).label('total'),
        func.sum(case((Driver.status == 'available', 1), else_=0)).label('available'),
        func.sum(case((Driver.status == 'on_trip', 1), else_=0)).label('on_trip'),
        func.sum(case((Driver.status == 'off_duty', 1), else_=0)).label('off_duty'),
        func.sum(case((Driver.status == 'suspended', 1), else_=0)).label('suspended')
    ).first()
    
    # Trip statistics
    trip_stats = db.query(
        func.count(Trip.id).label('total'),
        func.sum(case((Trip.status == 'draft', 1), else_=0)).label('draft'),
        func.sum(case((Trip.status == 'dispatched', 1), else_=0)).label('dispatched'),
        func.sum(case((Trip.status == 'completed', 1), else_=0)).label('completed'),
        func.sum(case((Trip.status == 'cancelled', 1), else_=0)).label('cancelled')
    ).first()
    
    # Maintenance statistics
    maintenance_stats = db.query(
        func.sum(case((Maintenance.status == 'scheduled', 1), else_=0)).label('scheduled'),
        func.sum(case((Maintenance.status == 'in_progress', 1), else_=0)).label('in_progress')
    ).first()
    
    # Monthly completed trips and distance
    monthly_trips = db.query(
        func.count(Trip.id).label('count'),
        func.coalesce(func.sum(Trip.actual_distance), 0).label('distance'),
        func.coalesce(func.sum(Trip.fuel_used), 0).label('fuel')
    ).filter(
        Trip.status == 'completed',
        Trip.completed_at >= start_of_month
    ).first()
    
    # Monthly fuel stats
    monthly_fuel = db.query(
        func.coalesce(func.sum(FuelLog.fuel_quantity), 0).label('quantity'),
        func.coalesce(func.sum(FuelLog.fuel_cost), 0).label('cost')
    ).filter(FuelLog.fuel_date >= start_of_month).first()
    
    # Monthly expenses by type
    expense_breakdown = db.query(
        Expense.expense_type,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.expense_date >= start_of_month
    ).group_by(Expense.expense_type).all()
    
    # Total operational cost
    total_expenses = db.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(Expense.expense_date >= start_of_month).scalar()
    
    # Recent trips
    recent_trips = db.query(Trip).order_by(Trip.created_at.desc()).limit(5).all()
    
    # Calculate KPIs
    total_active = (vehicle_stats.total or 0) - (vehicle_stats.retired or 0)
    fleet_utilization = round((vehicle_stats.on_trip or 0) / total_active * 100, 1) if total_active > 0 else 0
    
    total_distance = float(monthly_trips.distance or 0)
    total_fuel = float(monthly_trips.fuel or 0)
    fuel_efficiency = round(total_distance / total_fuel, 2) if total_fuel > 0 else 0
    
    return {
        "vehicles": {
            "total": vehicle_stats.total or 0,
            "active": (vehicle_stats.available or 0) + (vehicle_stats.on_trip or 0),
            "available": vehicle_stats.available or 0,
            "on_trip": vehicle_stats.on_trip or 0,
            "in_shop": vehicle_stats.in_shop or 0,
            "retired": vehicle_stats.retired or 0
        },
        "drivers": {
            "total": driver_stats.total or 0,
            "available": driver_stats.available or 0,
            "on_duty": driver_stats.on_trip or 0,
            "off_duty": driver_stats.off_duty or 0,
            "suspended": driver_stats.suspended or 0
        },
        "trips": {
            "total": trip_stats.total or 0,
            "active": trip_stats.dispatched or 0,
            "pending": trip_stats.draft or 0,
            "completed": trip_stats.completed or 0,
            "cancelled": trip_stats.cancelled or 0
        },
        "maintenance": {
            "scheduled": maintenance_stats.scheduled or 0,
            "in_progress": maintenance_stats.in_progress or 0
        },
        "monthly_stats": {
            "completed_trips": monthly_trips.count or 0,
            "total_distance": float(monthly_trips.distance or 0),
            "fuel_consumption": float(monthly_fuel.quantity or 0),
            "fuel_cost": float(monthly_fuel.cost or 0),
            "operational_cost": float(total_expenses or 0)
        },
        "expense_breakdown": [
            {"type": e.expense_type, "amount": float(e.total)}
            for e in expense_breakdown
        ],
        "kpis": {
            "fleet_utilization": fleet_utilization,
            "fuel_efficiency": fuel_efficiency,
            "vehicle_roi": 0  # Simplified
        },
        "recent_trips": [
            {
                "id": str(t.id),
                "trip_number": t.trip_number,
                "source": t.source,
                "destination": t.destination,
                "status": t.status,
                "created_at": t.created_at.isoformat()
            }
            for t in recent_trips
        ]
    }


@router.get("/analytics")
async def get_analytics(
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("analytics:view"))
):
    """Get analytics data"""
    today = date.today()
    
    if period == "week":
        start_date = today - timedelta(days=7)
    elif period == "quarter":
        start_date = date(today.year, ((today.month - 1) // 3) * 3 + 1, 1)
    elif period == "year":
        start_date = date(today.year, 1, 1)
    else:  # month
        start_date = date(today.year, today.month, 1)
    
    # Fuel by vehicle
    fuel_by_vehicle = db.query(
        FuelLog.vehicle_id,
        Vehicle.vehicle_name,
        Vehicle.registration_number,
        func.sum(FuelLog.fuel_quantity).label('total_fuel'),
        func.sum(FuelLog.fuel_cost).label('total_cost')
    ).join(Vehicle).filter(
        FuelLog.fuel_date >= start_date
    ).group_by(
        FuelLog.vehicle_id, Vehicle.vehicle_name, Vehicle.registration_number
    ).order_by(func.sum(FuelLog.fuel_quantity).desc()).limit(10).all()
    
    # Driver performance
    driver_performance = db.query(
        Trip.driver_id,
        Driver.first_name,
        Driver.last_name,
        Driver.safety_score,
        func.count(Trip.id).label('completed_trips'),
        func.sum(Trip.actual_distance).label('total_distance')
    ).join(Driver).filter(
        Trip.status == 'completed',
        Trip.completed_at >= datetime.combine(start_date, datetime.min.time())
    ).group_by(
        Trip.driver_id, Driver.first_name, Driver.last_name, Driver.safety_score
    ).order_by(func.count(Trip.id).desc()).limit(10).all()
    
    # Maintenance cost
    maintenance_cost = db.query(
        Maintenance.vehicle_id,
        Vehicle.vehicle_name,
        Vehicle.registration_number,
        func.sum(Maintenance.actual_cost).label('total_cost'),
        func.count(Maintenance.id).label('maintenance_count')
    ).join(Vehicle).filter(
        Maintenance.status == 'completed',
        Maintenance.completion_date >= start_date
    ).group_by(
        Maintenance.vehicle_id, Vehicle.vehicle_name, Vehicle.registration_number
    ).order_by(func.sum(Maintenance.actual_cost).desc()).limit(10).all()
    
    # Trip completion stats
    trip_stats = db.query(
        func.count(Trip.id).label('total'),
        func.sum(case((Trip.status == 'completed', 1), else_=0)).label('completed'),
        func.sum(case((Trip.status == 'cancelled', 1), else_=0)).label('cancelled')
    ).filter(Trip.created_at >= datetime.combine(start_date, datetime.min.time())).first()
    
    completion_rate = round((trip_stats.completed or 0) / (trip_stats.total or 1) * 100, 1)
    
    return {
        "fuel_by_vehicle": [
            {
                "vehicle_id": str(f.vehicle_id),
                "vehicle_name": f.vehicle_name,
                "registration_number": f.registration_number,
                "total_fuel": float(f.total_fuel or 0),
                "total_cost": float(f.total_cost or 0)
            }
            for f in fuel_by_vehicle
        ],
        "driver_performance": [
            {
                "driver_id": str(d.driver_id),
                "first_name": d.first_name,
                "last_name": d.last_name,
                "safety_score": d.safety_score,
                "completed_trips": d.completed_trips,
                "total_distance": float(d.total_distance or 0)
            }
            for d in driver_performance
        ],
        "maintenance_cost": [
            {
                "vehicle_id": str(m.vehicle_id),
                "vehicle_name": m.vehicle_name,
                "registration_number": m.registration_number,
                "total_cost": float(m.total_cost or 0),
                "maintenance_count": m.maintenance_count
            }
            for m in maintenance_cost
        ],
        "trip_completion": {
            "total": trip_stats.total or 0,
            "completed": trip_stats.completed or 0,
            "cancelled": trip_stats.cancelled or 0,
            "completion_rate": completion_rate
        },
        "vehicle_roi": []
    }


@router.post("/seed")
async def seed_database(db: Session = Depends(get_db)):
    """Seed database with sample data"""
    
    # Check if already seeded
    existing_user = db.query(User).filter(User.email == "admin@transitops.com").first()
    if existing_user:
        return {"message": "Database already seeded"}
    
    # Create users
    users_data = [
        {"email": "admin@transitops.com", "first_name": "System", "last_name": "Administrator", "role": "admin"},
        {"email": "fleet@transitops.com", "first_name": "John", "last_name": "Fleet", "role": "fleet_manager"},
        {"email": "dispatch@transitops.com", "first_name": "Sarah", "last_name": "Dispatch", "role": "dispatcher"},
        {"email": "safety@transitops.com", "first_name": "Mike", "last_name": "Safety", "role": "safety_officer"},
        {"email": "finance@transitops.com", "first_name": "Emily", "last_name": "Finance", "role": "financial_analyst"},
    ]
    
    hashed_password = hash_password("password123")
    
    for user_data in users_data:
        user = User(password=hashed_password, **user_data)
        db.add(user)
    
    # Create vehicles
    vehicles_data = [
        {"registration_number": "TRK-001", "vehicle_name": "Heavy Hauler Alpha", "vehicle_model": "Volvo FH16", "vehicle_type": "truck", "max_load_capacity": 25000, "odometer": 45230, "acquisition_cost": 150000, "manufacturer": "Volvo", "year": 2022, "fuel_type": "Diesel"},
        {"registration_number": "TRK-002", "vehicle_name": "Express Carrier", "vehicle_model": "Mercedes Actros", "vehicle_type": "truck", "max_load_capacity": 20000, "odometer": 32150, "acquisition_cost": 140000, "manufacturer": "Mercedes-Benz", "year": 2023, "fuel_type": "Diesel"},
        {"registration_number": "VAN-001", "vehicle_name": "City Runner", "vehicle_model": "Ford Transit", "vehicle_type": "van", "max_load_capacity": 3500, "odometer": 28400, "acquisition_cost": 45000, "manufacturer": "Ford", "year": 2023, "fuel_type": "Diesel"},
        {"registration_number": "VAN-002", "vehicle_name": "Quick Delivery", "vehicle_model": "Mercedes Sprinter", "vehicle_type": "van", "max_load_capacity": 4000, "odometer": 15600, "acquisition_cost": 52000, "manufacturer": "Mercedes-Benz", "year": 2024, "fuel_type": "Diesel"},
        {"registration_number": "TNK-001", "vehicle_name": "Fuel Master", "vehicle_model": "Scania R500", "vehicle_type": "tanker", "max_load_capacity": 30000, "odometer": 67800, "acquisition_cost": 180000, "manufacturer": "Scania", "year": 2021, "fuel_type": "Diesel", "status": "in_shop"},
        {"registration_number": "BUS-001", "vehicle_name": "Personnel Transport", "vehicle_model": "Volvo 9700", "vehicle_type": "bus", "max_load_capacity": 5000, "odometer": 89500, "acquisition_cost": 200000, "manufacturer": "Volvo", "year": 2020, "fuel_type": "Diesel"},
    ]
    
    for v_data in vehicles_data:
        vehicle = Vehicle(**v_data)
        db.add(vehicle)
    
    # Create drivers
    future_date = date.today() + timedelta(days=730)
    past_date = date.today() - timedelta(days=30)
    
    drivers_data = [
        {"first_name": "Robert", "last_name": "Johnson", "license_number": "DL-001-2024", "license_category": "CDL_A", "license_expiry": future_date, "contact_number": "+1-555-0101", "email": "robert.johnson@email.com", "safety_score": 95, "total_trips": 150, "total_distance": 45000},
        {"first_name": "Maria", "last_name": "Garcia", "license_number": "DL-002-2024", "license_category": "CDL_A", "license_expiry": future_date, "contact_number": "+1-555-0102", "email": "maria.garcia@email.com", "safety_score": 98, "total_trips": 200, "total_distance": 62000},
        {"first_name": "James", "last_name": "Wilson", "license_number": "DL-003-2024", "license_category": "CDL_B", "license_expiry": future_date, "contact_number": "+1-555-0103", "email": "james.wilson@email.com", "safety_score": 88, "total_trips": 120, "total_distance": 35000},
        {"first_name": "Linda", "last_name": "Martinez", "license_number": "DL-004-2024", "license_category": "CDL_A", "license_expiry": future_date, "contact_number": "+1-555-0104", "email": "linda.martinez@email.com", "safety_score": 92, "total_trips": 180, "total_distance": 55000, "status": "off_duty"},
        {"first_name": "David", "last_name": "Brown", "license_number": "DL-005-2024", "license_category": "C", "license_expiry": past_date, "contact_number": "+1-555-0105", "email": "david.brown@email.com", "safety_score": 75, "total_trips": 80, "total_distance": 22000},
        {"first_name": "Susan", "last_name": "Davis", "license_number": "DL-006-2024", "license_category": "CDL_A", "license_expiry": future_date, "contact_number": "+1-555-0106", "email": "susan.davis@email.com", "safety_score": 60, "total_trips": 50, "total_distance": 15000, "status": "suspended"},
    ]
    
    for d_data in drivers_data:
        driver = Driver(**d_data)
        db.add(driver)
    
    db.commit()
    
    return {
        "message": "Database seeded successfully",
        "credentials": {
            "admin": {"email": "admin@transitops.com", "password": "password123"},
            "fleet_manager": {"email": "fleet@transitops.com", "password": "password123"},
            "dispatcher": {"email": "dispatch@transitops.com", "password": "password123"},
            "safety_officer": {"email": "safety@transitops.com", "password": "password123"},
            "financial_analyst": {"email": "finance@transitops.com", "password": "password123"}
        }
    }
