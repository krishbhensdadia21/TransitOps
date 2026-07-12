"""
Dashboard Schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class VehicleStats(BaseModel):
    total: int
    active: int
    available: int
    on_trip: int
    in_shop: int
    retired: int


class DriverStats(BaseModel):
    total: int
    available: int
    on_duty: int
    off_duty: int
    suspended: int


class TripStats(BaseModel):
    total: int
    active: int
    pending: int
    completed: int
    cancelled: int


class MaintenanceStats(BaseModel):
    scheduled: int
    in_progress: int


class MonthlyStats(BaseModel):
    completed_trips: int
    total_distance: Decimal
    fuel_consumption: Decimal
    fuel_cost: Decimal
    operational_cost: Decimal


class ExpenseBreakdown(BaseModel):
    type: str
    amount: Decimal


class KPIs(BaseModel):
    fleet_utilization: float
    fuel_efficiency: Decimal
    vehicle_roi: Decimal


class RecentTrip(BaseModel):
    id: str
    trip_number: str
    source: str
    destination: str
    status: str
    created_at: datetime
    vehicle_registration: Optional[str] = None
    driver_name: Optional[str] = None


class DashboardResponse(BaseModel):
    vehicles: VehicleStats
    drivers: DriverStats
    trips: TripStats
    maintenance: MaintenanceStats
    monthly_stats: MonthlyStats
    expense_breakdown: List[ExpenseBreakdown]
    kpis: KPIs
    recent_trips: List[RecentTrip]


class AnalyticsResponse(BaseModel):
    fuel_by_vehicle: List[dict]
    driver_performance: List[dict]
    maintenance_cost: List[dict]
    trip_completion: dict
    vehicle_roi: List[dict]
    expense_trends: List[dict]
