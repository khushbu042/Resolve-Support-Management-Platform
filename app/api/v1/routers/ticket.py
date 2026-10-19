from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import Permission, get_current_user, require_permission
from app.db.database import get_db
from app.api.schemas.ticket import (
    CreateTicketRequest, TicketListResponse, TicketResponse, UpdateTicketRequest, AssignTicketRequest
)
from app.api.schemas.common import MessageResponse
from app.services.ticket_service import (
    create_ticket,
    delete_ticket,
    get_all_tickets,
    update_ticket,
    assign_ticket,
)
from app.database_model.user_model import User
router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "/ticket", 
    response_model=TicketResponse,
    summary="Create a new ticket",
    description="Create a new ticket with the given details",
)
async def create_ticket_api(
    ticket: CreateTicketRequest,
    user_permission: Permission = Depends(require_permission(Permission.TICKET_CREATE)),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_ticket(ticket,user_permission,current_user, db)

@router.get(
    "/tickets", 
    # response_model=TicketListResponse,
    summary="Get all tickets",
    description="Get all tickets for admin or agent"
)
async def get_all_tickets_api(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("asc"),
    user_permission: Permission = Depends(require_permission(Permission.TICKET_READ_ALL)),
    db: AsyncSession = Depends(get_db),
):
    return await get_all_tickets(page, limit, sort_by, order, user_permission, db)

@router.patch(
    "/tickets/{ticket_id}/assign", 
    response_model= TicketResponse,
    summary="Only admin can assign a ticket to an agent",
    description="Only admin can assign a ticket to an agent with the given details",
)
async def assign_ticket_api(
    ticket_id: int,
    assignee: AssignTicketRequest,
    user_permission: Permission = Depends(require_permission(Permission.TICKET_ASSIGN)),
    db: AsyncSession = Depends(get_db),
):
    return await assign_ticket(
        ticket_id,
        assignee,
        db
    )

@router.patch(
    "/tickets/{ticket_id}", 
    response_model=TicketResponse,
    summary="The ticket owner or admin can update a ticket",
    description="The ticket owner or admin can update a ticket with the given details",
)
async def update_ticket_api(
    ticket_id: int,
    ticket: UpdateTicketRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.permissions import ROLE_PERMISSIONS
    permissions = ROLE_PERMISSIONS.get(current_user.role.value, set())

    if Permission.TICKET_UPDATE_ANY in permissions:
        return await update_ticket(ticket_id, ticket, current_user, db)

    if Permission.TICKET_UPDATE_OWN in permissions:
        return await update_ticket(ticket_id, ticket, current_user, db, owner_only=True)

    raise HTTPException(status_code=403, detail="Not authorized to update this ticket")

@router.delete(
    "/tickets/{ticket_id}", 
    response_model=MessageResponse,
    summary="Only admin can delete a ticket",
    description="Only admin can delete a ticket.",
)
async def delete_ticket_api(
    ticket_id: int,
    user_permission: Permission = Depends(require_permission(Permission.TICKET_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    return await delete_ticket(ticket_id, user_permission, db)


# ---------------------------- Bulk Operations ----------------------------

# @router.post("/tickets/bulk")
# def bulk_create_tickets_api(
#     tickets: list[CreateTicketRequest],
#     current_user=Depends(require_permission(Permission.TICKET_CREATE)),
#     db: Session = Depends(get_db),
# ):
#     return bulk_create_tickets(tickets, current_user, db)

# @router.delete("/tickets/bulk")
# def bulk_delete_tickets_api(
#     tickets: list[BulkDeleteTicketRequest],
#     current_user=Depends(require_permission(Permission.TICKET_DELETE)),
#     db: Session = Depends(get_db),
# ):
#     return bulk_delete_tickets(tickets, current_user, db)

# @router.patch("/tickets/bulk")
# def bulk_update_ticket_api(
#     tickets: list[BulkUpdateTicketRequest],
#     current_user=Depends(require_permission(Permission.TICKET_UPDATE_ANY)),
#     db: Session = Depends(get_db),
# ):
#     return bulk_update_tickets(tickets, current_user, db)