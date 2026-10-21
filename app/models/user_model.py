from sqlalchemy import (
    Column, Integer, String, Text, Boolean, 
    ForeignKey, DateTime, Enum, BigInteger
)
from datetime import datetime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.database import Base
import enum


# ── User roles ───────────────────────────────────────────────
class UserRole(str, enum.Enum):
    customer = "customer"
    agent = "agent"
    admin = "admin"

# ── User model ───────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.agent
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    # tickets this user CREATED (as customer)
    tickets_created = relationship(
        "Ticket",
        foreign_keys="Ticket.customer_id",
        back_populates="customer"
    )

    tickets_assigned = relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_agent_id",
        back_populates="assigned_agent",
    )

    comments = relationship(
        "TicketComment",
        back_populates="sender",
    )

    attachments = relationship(
        "TicketAttachment",
        back_populates="uploader",
    )



