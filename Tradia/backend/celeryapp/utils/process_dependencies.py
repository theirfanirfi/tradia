from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Annotated
from config.database import get_db
from models import UserProcess
from models.auth import User
from utils.auth_dependencies import get_current_active_user


async def get_user_process(
    process_id: Annotated[str, Path(description="The process ID")],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserProcess:
    """
    Dependency to get a process that belongs to the current user.
    
    Args:
        process_id: The ID of the process to retrieve
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        UserProcess: The process if it belongs to the user
        
    Raises:
        HTTPException: If process not found or doesn't belong to user
    """
    process = db.query(UserProcess).filter(
        UserProcess.process_id == process_id,
        UserProcess.user_id == current_user.user_id
    ).first()
    
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process not found or access denied"
        )
    
    return process


async def get_user_process_optional(
    process_id: Annotated[str, Path(description="The process ID")],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserProcess | None:
    """
    Dependency to get a process that belongs to the current user (optional).
    
    Args:
        process_id: The ID of the process to retrieve
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        UserProcess | None: The process if it exists and belongs to user, None otherwise
    """
    process = db.query(UserProcess).filter(
        UserProcess.process_id == process_id,
        UserProcess.user_id == current_user.user_id
    ).first()
    
    return process


def verify_process_ownership(
    process: UserProcess,
    user_id: str
) -> bool:
    """
    Utility function to verify if a process belongs to a specific user.
    
    Args:
        process: The process to check
        user_id: The user ID to verify against
        
    Returns:
        bool: True if process belongs to user, False otherwise
    """
    return process.user_id == user_id


async def get_user_process_by_name(
    process_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserProcess:
    """
    Dependency to get a process by name that belongs to the current user.
    
    Args:
        process_name: The name of the process to retrieve
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        UserProcess: The process if it belongs to the user
        
    Raises:
        HTTPException: If process not found or doesn't belong to user
    """
    process = db.query(UserProcess).filter(
        UserProcess.process_name == process_name,
        UserProcess.user_id == current_user.user_id
    ).first()
    
    if not process:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Process '{process_name}' not found or access denied"
        )
    
    return process


class ProcessPermissionChecker:
    """
    Class-based dependency for more complex process permission checking
    """
    
    def __init__(self, allow_admin: bool = False, require_status: str = None):
        self.allow_admin = allow_admin
        self.require_status = require_status
    
    async def __call__(
        self,
        process_id: Annotated[str, Path(description="The process ID")],
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> UserProcess:
        """
        Check process permissions with additional conditions
        
        Args:
            process_id: The ID of the process
            current_user: The current authenticated user
            db: Database session
            
        Returns:
            UserProcess: The process if permissions are valid
            
        Raises:
            HTTPException: If access is denied or conditions not met
        """
        # Check if user has admin privileges (if implemented)
        if self.allow_admin and hasattr(current_user, 'is_admin') and current_user.is_admin:
            process = db.query(UserProcess).filter(
                UserProcess.process_id == process_id
            ).first()
        else:
            # Regular user - check ownership
            process = db.query(UserProcess).filter(
                UserProcess.process_id == process_id,
                UserProcess.user_id == current_user.user_id
            ).first()
        
        if not process:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Process not found or access denied"
            )
        
        # Check status requirement if specified
        if self.require_status and process.status.value != self.require_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Process must be in '{self.require_status}' status"
            )
        
        return process


# Predefined permission checkers for common use cases
require_user_process = ProcessPermissionChecker()
require_active_process = ProcessPermissionChecker(require_status="ACTIVE")
require_created_process = ProcessPermissionChecker(require_status="CREATED")
admin_or_owner_process = ProcessPermissionChecker(allow_admin=True)


async def bulk_verify_process_ownership(
    process_ids: list[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> list[UserProcess]:
    """
    Dependency to verify ownership of multiple processes at once.
    
    Args:
        process_ids: List of process IDs to check
        current_user: The current authenticated user
        db: Database session
    
    Returns:
        list[UserProcess]: List of processes that belong to the user
        
    Raises:
        HTTPException: If any process is not found or doesn't belong to user
    """
    if not process_ids:
        return []
    
    processes = db.query(UserProcess).filter(
        UserProcess.process_id.in_(process_ids),
        UserProcess.user_id == current_user.user_id
    ).all()
    
    if len(processes) != len(process_ids):
        found_ids = {p.process_id for p in processes}
        missing_ids = set(process_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processes not found or access denied: {', '.join(missing_ids)}"
        )
    
    return processes


# Convenience functions for common patterns
def get_process_owner_dependency(process_id_param: str = "process_id"):
    """
    Factory function to create process ownership dependency with custom parameter name
    
    Args:
        process_id_param: Name of the path parameter containing process ID
        
    Returns:
        Dependency function
    """
    async def check_process_ownership(
        process_id: str = Path(..., alias=process_id_param),
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> UserProcess:
        return await get_user_process(process_id, current_user, db)
    
    return check_process_ownership



"""
example usage
@router.delete("/{process_id}")
async def delete_process(
    process: UserProcess = Depends(get_user_process),
    db: Session = Depends(get_db)
):
"""