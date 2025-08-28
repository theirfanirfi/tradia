from .user_process import UserProcess, ProcessStatus
from .user_declaration import UserDeclaration, DeclarationType
from .user_documents import UserDocument
from .user_process_items import UserProcessItem
from .auth import User, RefreshToken
from sqlalchemy.orm import relationship

# Establish relationships
UserProcess.declarations = relationship("UserDeclaration", back_populates="process", cascade="all, delete-orphan")
UserProcess.documents = relationship("UserDocument", back_populates="process", cascade="all, delete-orphan")
UserProcess.items = relationship("UserProcessItem", back_populates="process", cascade="all, delete-orphan")

__all__ = [
    "UserProcess",
    "ProcessStatus", 
    "UserDeclaration",
    "DeclarationType",
    "UserDocument",
    "UserProcessItem",
    "User",
    "RefreshToken",
]
