from typing import Dict, Any
from models import UserProcess, ProcessStatus
from config.database import SessionLocal
from sqlalchemy.sql import func


def update_process_status(process_id: str, status: ProcessStatus, message: str = None):
    """Update process status in database"""
    db = SessionLocal()
    try:
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if process:
            process.status = status
            process.updated_at = func.now()
            db.commit()
    except Exception as e:
        print(f"Status update error: {e}")
    finally:
        db.close()


def calculate_progress(process_id: str) -> int:
    """Calculate process progress percentage"""
    db = SessionLocal()
    try:
        # Get process and related documents
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if not process:
            return 0
        
        # Get total documents for this process
        from models import UserDocument
        total_docs = db.query(UserDocument).filter(UserDocument.process_id == process_id).count()
        
        if total_docs == 0:
            return 0
        
        # Get processed documents
        processed_docs = db.query(UserDocument).filter(
            UserDocument.process_id == process_id,
            UserDocument.processed_at.isnot(None)
        ).count()
        
        # Calculate progress based on status and document processing
        if process.status == ProcessStatus.CREATED:
            return 0
        elif process.status == ProcessStatus.EXTRACTING:
            return min(25, int((processed_docs / total_docs) * 25))
        elif process.status == ProcessStatus.UNDERSTANDING:
            return min(75, 25 + int((processed_docs / total_docs) * 50))
        elif process.status == ProcessStatus.GENERATING:
            return 90
        elif process.status == ProcessStatus.DONE:
            return 100
        elif process.status == ProcessStatus.ERROR:
            return 0
        
        return 0
        
    except Exception as e:
        print(f"Progress calculation error: {e}")
        return 0
    finally:
        db.close()


def get_process_summary(process_id: str) -> Dict[str, Any]:
    """Get comprehensive process summary"""
    db = SessionLocal()
    try:
        from models import UserDocument, UserProcessItem, UserDeclaration
        
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if not process:
            return {}
        
        # Get counts
        doc_count = db.query(UserDocument).filter(UserDocument.process_id == process_id).count()
        processed_doc_count = db.query(UserDocument).filter(
            UserDocument.process_id == process_id,
            UserDocument.processed_at.isnot(None)
        ).count()
        item_count = db.query(UserProcessItem).filter(UserProcessItem.process_id == process_id).count()
        
        # Get declaration
        declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
        
        return {
            "process_id": str(process.process_id),
            "process_name": process.process_name,
            "status": process.status.value,
            "created_at": process.created_at.isoformat() if process.created_at else None,
            "updated_at": process.updated_at.isoformat() if process.updated_at else None,
            "documents": {
                "total": doc_count,
                "processed": processed_doc_count,
                "pending": doc_count - processed_doc_count
            },
            "items": item_count,
            "declaration_type": declaration.declaration_type.value if declaration else None,
            "progress": calculate_progress(process_id)
        }
        
    except Exception as e:
        print(f"Process summary error: {e}")
        return {}
    finally:
        db.close()
