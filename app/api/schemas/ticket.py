from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.database_model.ticket_model import (
    AttachmentStatus,
    TicketPriority,
    TicketStatus,
)

class TicketAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    comment_id: int | None = None
    uploaded_by: int
    file_name: str
    file_url: str
    file_type: str
    file_size: int
    status: AttachmentStatus
    created_at: datetime


class TicketAttachmentDownloadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    content_type: str
    file_size: int
    download_url: str


class CreateTicketRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: TicketPriority = TicketPriority.medium

class AssignTicketRequest(BaseModel):
    assignee: int
   
class UpdateTicketRequest(BaseModel):
    title: str | None = None
    description: str | None = None 
    status: TicketStatus | None = None
    priority: TicketPriority | None = None

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    customer_id: int
    assigned_agent_id: int | None = None

class TicketListResponse(BaseModel):
    page: int
    limit: int
    # total: int
    # total_pages: int
    data: list[TicketResponse]


class BulkUpdateTicketRequest(BaseModel):
    id: int
    title: str | None = None
    description: str | None = None


class BulkDeleteTicketRequest(BaseModel):
    id: int

class TicketAssignedEvent(BaseModel):
    ticket_id: int
    ticket_title: str
    agent_id: int
    agent_name: str
    agent_email: EmailStr
    assigned_by_id: int | None = None
    assigned_at: datetime
    message_id: str = Field(..., min_length=1)


