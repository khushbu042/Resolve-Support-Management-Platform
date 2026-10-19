from app.api.v1.routers.ticket import router as ticket_router
# from app.api.v1.routers.user import router as user_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.ticket_attachments import router as ticket_attachments_router

__all__ = ["ticket_router", "auth_router", "ticket_attachments_router"]