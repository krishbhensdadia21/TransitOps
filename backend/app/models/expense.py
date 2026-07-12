"""
Expense Model
"""
from sqlalchemy import Column, String, Numeric, DateTime, Text, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from backend.app.core.database import Base


class ExpenseType(str, enum.Enum):
    FUEL = "fuel"
    MAINTENANCE = "maintenance"
    TOLL = "toll"
    INSURANCE = "insurance"
    REGISTRATION = "registration"
    SALARY = "salary"
    OTHER = "other"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True, index=True)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=True, index=True)
    expense_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    expense_date = Column(Date, nullable=False, index=True)
    vendor = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    receipt_url = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="expenses")
    trip = relationship("Trip", back_populates="expenses")

    def __repr__(self):
        return f"<Expense {self.id}>"
