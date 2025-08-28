from pydantic import BaseModel, EmailStr
from uuid import UUID
class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
class UserCreate(UserBase):
    password: str
class UserRead(UserBase):
    id: UUID
    is_active: bool
    is_superuser: bool
    class Config:
        from_attributes = True