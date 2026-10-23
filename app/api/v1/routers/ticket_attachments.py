from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.ticket import (
    TicketAttachmentDownloadResponse,
    TicketAttachmentResponse,
)
from app.auth import Permission, get_current_user, require_permission
from app.db.database import get_db
from app.models.user_model import User
from app.services.ticket_attachments_service import (
    download_attachment,
    get_ticket_attachments,
    upload_attachment,
)

router = APIRouter(prefix="/tickets/attachments", tags=["Ticket Attachments"])


@router.post(
    "/{ticket_id}",
    summary="Any user can upload a file to a ticket",
    description="Any user can upload a file to a ticket with the given details",
    response_model=TicketAttachmentResponse,
)
async def upload_attachment_api(
    ticket_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await upload_attachment(ticket_id, file, current_user, db)


@router.get(
    "/tickets/{ticket_id}/attachments",
    summary="Any user can get all attachments for a ticket",
    description="Any user can get all attachments for a ticket with the given details",
    response_model=list[TicketAttachmentResponse],
)
async def get_ticket_attachments_api(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_ticket_attachments(ticket_id, current_user, db)


@router.get(
    "/{attachment_id}/download",
    summary="Any user can download an attachment using the attachment id",
    description="Any user can download an attachment using the attachment id",
    response_model=TicketAttachmentDownloadResponse,
)
async def download_attachment_api(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await download_attachment(attachment_id, current_user, db)
