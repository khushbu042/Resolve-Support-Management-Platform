import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.common import MessageResponse
from app.api.schemas.ticket import (
    AttachmentStatus,
    TicketAttachmentDownloadResponse,
    TicketAttachmentResponse,
)
from app.core.permissions import Permission
from app.core.settings import get_settings
from app.models.ticket_model import Ticket, TicketAttachment
from app.models.user_model import User
from app.services.s3_service import delete_file, generate_download_url, upload_file

settings = get_settings()
ALLOWED_FILES = settings.allowed_files
MAX_FILE_SIZE = settings.max_file_size
CHUNK_SIZE = settings.chunk_size


async def upload_attachment(
    ticket_id: int,
    file: UploadFile,
    current_user: User,
    db: AsyncSession,
):
    select_ticket = select(Ticket).filter(Ticket.id == ticket_id)
    result = await db.execute(select_ticket)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket Not found")

    original_filename = file.filename or ""
    extension = os.path.splitext(original_filename)[1].lower()

    if extension not in ALLOWED_FILES:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    if file.content_type != ALLOWED_FILES[extension]:
        raise HTTPException(
            status_code=400, detail="File extension and content type do not match"
        )

    safe_filename = f"{uuid4()}{extension}"
    object_key = f"tickets/{ticket.id}/{safe_filename}"

    file_size = 0

    try:
        while True:
            chunk = file.file.read(CHUNK_SIZE)

            if not chunk:
                break

            file_size += len(chunk)

            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413, detail="File size exceeds 5 MB limit"
                )

        file.file.seek(0)

        await upload_file(
            file.file,
            object_key,
        )

    except Exception:
        delete_file(object_key)
        raise

    attachment = TicketAttachment(
        ticket_id=ticket_id,
        uploaded_by=current_user.id,
        file_name=original_filename,
        file_url=object_key,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        status="uploading",
    )

    try:
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
    except Exception:
        await db.rollback()
        delete_file(object_key)
        raise

    return TicketAttachmentResponse.model_validate(attachment)


async def get_ticket_attachments(
    ticket_id: int,
    current_user: User,
    db: AsyncSession,
):
    select_ticket = select(Ticket).filter(Ticket.id == ticket_id)
    result = await db.execute(select_ticket)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    select_attachments = select(TicketAttachment).filter(
        TicketAttachment.ticket_id == ticket_id
    )
    result = await db.execute(select_attachments)
    attachments = result.scalars().all()

    return [
        TicketAttachmentResponse.model_validate(attachment)
        for attachment in attachments
    ]


async def download_attachment(
    attachment_id: int,
    current_user: User,
    db: AsyncSession,
):
    select_attachment = select(TicketAttachment).filter(
        TicketAttachment.id == attachment_id
    )
    result = await db.execute(select_attachment)
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Attachment not found",
        )

    download_url = await generate_download_url(attachment.file_url)
    return TicketAttachmentDownloadResponse(
        filename=attachment.file_name,
        content_type=attachment.file_type,
        file_size=attachment.file_size,
        download_url=download_url,
    )


async def delete_attachment(
    attachment_id: int,
    current_user: User,
    db: AsyncSession,
):
    select_attachment = select(TicketAttachment).filter(
        TicketAttachment.id == attachment_id
    )
    result = await db.execute(select_attachment)
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Attachment not found",
        )

    ticket = db.get(Ticket, attachment.ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if ticket.customer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this attachment",
        )

    file_path = Path(attachment.file_url)

    if file_path.exists():
        file_path.unlink()

    try:
        db.delete(attachment)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Attachment deleted successfully"}
