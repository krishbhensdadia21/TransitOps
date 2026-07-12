"""
Fuel Log Model
"""
from sqlalchemy import Column, String, Numeric, DateTime, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from backend.app.core.database import Base


class FuelLog(Base):
    __tablename__ = "fuel_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=True, index=True)
    fuel_quantity = Column(Numeric(10, 2), nullable=False)
    fuel_cost = Column(Numeric(15, 2), nullable=False)
    price_per_unit = Column(Numeric(10, 4), nullable=True)
    fuel_type = Column(String(50), nullable=False)
    odometer_reading = Column(Numeric(12, 2), nullable=True)
    fuel_station = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    fuel_date = Column(Date, nullable=False)
    receipt_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="fuel_logs")
    trip = relationship("Trip", back_populates="fuel_logs")

    def __repr__(self):
        return f"<FuelLog {self.id}>"
