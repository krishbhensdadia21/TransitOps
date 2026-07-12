"""
Vehicle Model
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from backend.app.core.database import Base


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    IN_SHOP = "in_shop"
    RETIRED = "retired"


class VehicleType(str, enum.Enum):
    TRUCK = "truck"
    VAN = "van"
    BUS = "bus"
    TRAILER = "trailer"
    TANKER = "tanker"
    PICKUP = "pickup"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_number = Column(String(50), unique=True, nullable=False, index=True)
    vehicle_name = Column(String(100), nullable=False)
    vehicle_model = Column(String(100), nullable=False)
    vehicle_type = Column(String(50), nullable=False)
    max_load_capacity = Column(Numeric(10, 2), nullable=False)
    odometer = Column(Numeric(12, 2), nullable=False, default=0)
    acquisition_cost = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), nullable=False, default="available", index=True)
    manufacturer = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    fuel_type = Column(String(50), nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    last_service_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trips = relationship("Trip", back_populates="vehicle")
    maintenance_records = relationship("Maintenance", back_populates="vehicle")
    fuel_logs = relationship("FuelLog", back_populates="vehicle")
    expenses = relationship("Expense", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle {self.registration_number}>"
