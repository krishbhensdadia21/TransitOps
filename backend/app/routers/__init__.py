"""
API Routers
"""
from .auth import router as auth_router
from .vehicles import router as vehicles_router
from .drivers import router as drivers_router
from .trips import router as trips_router
from .maintenance import router as maintenance_router
from .fuel import router as fuel_router
from .expenses import router as expenses_router
from .dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "vehicles_router",
    "drivers_router",
    "trips_router",
    "maintenance_router",
    "fuel_router",
    "expenses_router",
    "dashboard_router"
]
