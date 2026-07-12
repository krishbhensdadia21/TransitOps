"""
Maintenance Model
"""
from sqlalchemy import Column, String, Numeric, DateTime, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from backend.app.core.database import Base


class MaintenanceStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False, index=True)
    maintenance_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    estimated_cost = Column(Numeric(15, 2), nullable=True)
    actual_cost = Column(Numeric(15, 2), nullable=True)
    odometer_at_service = Column(Numeric(12, 2), nullable=True)
    service_provider = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="scheduled", index=True)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="maintenance_records")

    def __repr__(self):
        return f"<Maintenance {self.id}>"
