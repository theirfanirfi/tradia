from .process import router as process_router
from .documents import router as documents_router
from .items import router as items_router
from .declarations import router as declarations_router

__all__ = [
    "process_router",
    "documents_router",
    "items_router",
    "declarations_router"
]
