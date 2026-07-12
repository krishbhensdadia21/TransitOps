"""
Driver Model
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from backend.app.core.database import Base


class DriverStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    OFF_DUTY = "off_duty"
    SUSPENDED = "suspended"


class LicenseCategory(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    CDL_A = "CDL_A"
    CDL_B = "CDL_B"
    CDL_C = "CDL_C"


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    license_category = Column(String(20), nullable=False)
    license_expiry = Column(Date, nullable=False)
    contact_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(20), nullable=True)
    safety_score = Column(Integer, nullable=False, default=100)
    total_trips = Column(Integer, nullable=False, default=0)
    total_distance = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(20), nullable=False, default="available", index=True)
    date_of_birth = Column(Date, nullable=True)
    hire_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trips = relationship("Trip", back_populates="driver")

    def __repr__(self):
        return f"<Driver {self.first_name} {self.last_name}>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
