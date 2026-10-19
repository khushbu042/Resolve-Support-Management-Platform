import logging
import math
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.rabbitmq.publisher import publish_ticket_assigned
from fastapi.responses import StreamingResponse
from app.database_model.user_model import User
from sqlalchemy import select
from app.database_model.ticket_model import (
    AttachmentStatus,
    Ticket,
    TicketAttachment,
    TicketPriority,
    TicketStatus,
)
from app.database_model.user_model import User
from app.api.schemas.ticket import (
    CreateTicketRequest,
    UpdateTicketRequest,
    AssignTicketRequest,
    TicketResponse,
)
from app.core.permissions import Permission
from app.api.schemas.common import MessageResponse

UPLOAD_DIR = Path("app/uploads/tickets")

logger = logging.getLogger(__name__)

async def create_ticket(
    ticket: CreateTicketRequest, 
    user_permission, 
    current_user: User, 
    db: AsyncSession
):
    
    new_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        status=TicketStatus.open,
        priority=ticket.priority,
        customer_id=current_user.id,
    )

    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)

    return TicketResponse(
        id=new_ticket.id,
        title=new_ticket.title,
        description=new_ticket.description,
        status=new_ticket.status,
        priority=new_ticket.priority,
        customer_id=new_ticket.customer_id,
    )

async def assign_ticket(
    ticket_id: int,
    assignee: AssignTicketRequest,
    db: AsyncSession,
):
    ticket = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    ticket = ticket.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    assignee_user = await db.execute(select(User).filter(User.id == assignee.assignee))
    assignee_user = assignee_user.scalar_one_or_none()
    if not assignee_user:
        raise HTTPException(status_code=404, detail="Assignee not found")

    # optional but recommended: only allow assigning to users with an "agent"/"admin" role
    if assignee_user.role not in ("agent", "admin"):
        raise HTTPException(status_code=400, detail="User is not eligible to be assigned tickets")

    ticket.assigned_agent_id= assignee.assignee

    if ticket.status == TicketStatus.open:
        ticket.status = TicketStatus.pending

    await db.commit()
    await db.refresh(ticket)

    try:
        await publish_ticket_assigned(ticket, assignee_user, assigned_by_id=assignee.assignee)
    except Exception:
        logger.exception(
            "Ticket %s assigned but notification event was not published",
            ticket.id,
        )

    return ticket

async def update_ticket(
    ticket_id: int,
    ticket_update: UpdateTicketRequest,
    current_user: User,
    db: AsyncSession,
    owner_only: bool = False,
):
    existing_ticket = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    existing_ticket = existing_ticket.scalar_one_or_none()

    if not existing_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if owner_only:
        if existing_ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You don't have permission to update this ticket."
            )

    update_data = ticket_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    for key, value in update_data.items():
        setattr(existing_ticket, key, value)

    try:
        await db.commit()
        await db.refresh(existing_ticket)
    except Exception:
        await db.rollback()
        raise

    return existing_ticket

async def delete_ticket(
    ticket_id: int, 
    user_permission: Permission, 
    db: AsyncSession
):
    ticket = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
    ticket = ticket.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    await db.delete(ticket)
    await db.commit()

    return MessageResponse(message="Ticket deleted successfully")

async def get_all_tickets(
    page, 
    limit, 
    sort_by, 
    order, 
    user_permission, 
    db: AsyncSession
):
    """
        Fetch all tickets across customers for authorized administrators
        and agents, with pagination and sorting.
    """

    # Define allowed sorting fields.
    allowed_sort_fields = {
        "status": Ticket.status,
        "priority": Ticket.priority,
        "created_at": Ticket.created_at,
    }
    
    allowed_orders = {"asc", "desc"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if order not in allowed_orders:
        raise HTTPException(status_code=400, detail="Invalid order field")

    # Calculate offset for pagination.      
    offset = (page - 1) * limit

    # Build the base query for all tickets.
    base_query = select(Ticket)

    # Apply sorting.
    sort_column = allowed_sort_fields[sort_by]

    sort_expression = (
        sort_column.asc()
        if order == "asc"
        else sort_column.desc()
    )

    # Add a secondary sort for predictable pagination.
    ticket_query = (
        base_query
        .options(
            selectinload(Ticket.customer),
            selectinload(Ticket.assigned_agent),
        )
        .order_by(sort_expression, Ticket.id.asc())
        .offset(offset)
        .limit(limit)
    )

    # Execute the asynchronous query.
    result = await db.execute(ticket_query)
    existing_tickets = result.scalars().all()

    # Calculate total pages.
    # total_pages = math.ceil(total_count / limit) if total_count else 0

    # Return the paginated result.
    return {
        "page": page,
        "limit": limit,
        # "total": total_count,
        # "total_pages": total_pages,
        "data": existing_tickets,
    }


# def bulk_create_tickets(
#     tickets: list[CreateTicketRequest],
#     current_user: User,
#     db: Session,
# ):
#     if not tickets:
#         raise HTTPException(status_code=400, detail=" At least one ticket is required.")

#     ticket_objects = []

#     for ticket in tickets:
#         if ticket.customer_id != current_user.id:
#             raise HTTPException(
#                 status_code=403,
#                 detail="You can only create tickets for your own customer account.",
#             )

#         new_ticket = Ticket(
#             title=ticket.title,
#             description=ticket.description,
#             status=ticket.status,
#             priority=ticket.priority,
#             customer_id=ticket.customer_id,
#             assigned_agent_id=ticket.assigned_agent_id,
#             sla_deadline=ticket.sla_deadline,
#         )
#         ticket_objects.append(new_ticket)

#     try:
#         db.add_all(ticket_objects)
#         db.commit()
#     except Exception:
#         db.rollback()
#         raise

#     return ticket_objects


# def bulk_update_tickets(
#     update_tickets: list[BulkUpdateTicketRequest],
#     current_user: User,
#     db: Session,
# ):
#     if not update_tickets:
#         raise HTTPException(
#             status_code=400, detail=" At least one ticket is required to update"
#         )

#     requested_ticket_ids = {update.id for update in update_tickets}

#     tickets = db.query(Ticket).filter(Ticket.id.in_(requested_ticket_ids)).all()

#     db_ticket_ids = {ticket.id for ticket in tickets}

#     missing_ids = requested_ticket_ids - db_ticket_ids

#     if missing_ids:
#         raise HTTPException(
#             status_code=404, detail=f"Tickets not found: {list(missing_ids)}"
#         )

#     for ticket in tickets:
#         if ticket.customer_id != current_user.id:
#             raise HTTPException(
#                 status_code=403, detail="Not authorized to update one or more tickets"
#             )

#     ticket_map = {ticket.id: ticket for ticket in tickets}

#     for update in update_tickets:
#         ticket = ticket_map[update.id]

#         update_data = update.model_dump(exclude_unset=True, exclude={"id"})

#         for key, value in update_data.items():
#             setattr(ticket, key, value)

#     try:
#         db.commit()
#         db.refresh(tickets)
#     except Exception:
#         db.rollback()
#         raise

#     return tickets


# def bulk_delete_tickets(
#     delete_tickets: list[BulkDeleteTicketRequest],
#     current_user: User,
#     db: Session,
# ):
    # if not delete_tickets:
    #     raise HTTPException(
    #         status_code=400, detail=" At least one ticket is required to delete"
    #     )

    # unique_delete_ids = {ticket.id for ticket in delete_tickets}

    # db_tickets = db.query(Ticket).filter(Ticket.id.in_(unique_delete_ids)).all()

    # db_ticket_ids = {ticket.id for ticket in db_tickets}

    # missing_ids = unique_delete_ids - db_ticket_ids

    # if missing_ids:
    #     raise HTTPException(
    #         status_code=404, detail=f"Tickets not found: {list(missing_ids)}"
    #     )

    # for ticket in db_tickets:
    #     if ticket.customer_id != current_user.id:
    #         raise HTTPException(
    #             status_code=403,
    #             detail="Not authorized to delete one or more tickets",
    #         )

    # deleted_count = (
    #     db.query(Ticket)
    #     .filter(Ticket.id.in_(unique_delete_ids))
    #     .delete(synchronize_session=False)
    # )

    # try:
    #     db.commit()
    # except Exception:
    #     db.rollback()
    #     raise

    # return {"message": f"{deleted_count} tickets deleted successfully"}