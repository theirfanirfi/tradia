from anyio import sleep
from celery import Celery
from typing import List
import json
from config.settings import settings
from services.ocr_service import ocr_service
from services.llm_service import llm_service
from models import UserDocument, UserProcessItem, UserProcess, ProcessStatus
from config.database import SessionLocal
from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger


# Initialize Celery
celery_app = Celery(
    "customs_tasks",
    broker=settings.redis_url+'/0',
    backend=settings.redis_url+'/1'
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

logger = get_task_logger(__name__)

@celery_app.task
def process_documents(process_id: str, document_ids: List[str]):
    """Background task to process uploaded documents"""
    db = SessionLocal()
    print('documents processing')
    
    try:
        # Update process status to 'extracting'
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if process:
            process.status = ProcessStatus.EXTRACTING
            db.commit()
    
        print(f"Processing documents for process ID: {process_id} with document IDs: {document_ids}")
        # Process each document
        for doc_id in document_ids:
            try:
                # Get document
                document = db.query(UserDocument).filter(UserDocument.document_id == doc_id).first()
                if not document:
                    print('document not found')
                
                # OCR extraction
                ocr_text = ocr_service.extract_text_hybrid(document.file_path)
                if ocr_text:
                    document.ocr_text = ocr_text
                
                # Update status to 'understanding'
                if process:
                    process.status = ProcessStatus.UNDERSTANDING
                    db.commit()

                # LLM processing
                llm_response = llm_service.process_item_extract_document(
                    ocr_text, 
                    process_id,
                    "import"  # Default to import, can be enhanced
                )
                print(f"LLM response: {llm_response}")
                
                if llm_response:
                    document.llm_response = llm_response
                    document.processed_at = db.query(func.now()).scalar()
                    process.status = ProcessStatus.EXTRACTING
                    db.commit()
                    
                    
            #         # Extract items from LLM response
            #         if 'items' in llm_response:
            #             for item_data in llm_response['items']:
            #                 item = UserProcessItem(
            #                     process_id=process_id,
            #                     item_title=item_data.get('item_title', 'Unknown Item'),
            #                     item_description=item_data.get('item_description'),
            #                     item_type=item_data.get('item_type'),
            #                     item_weight=item_data.get('item_weight'),
            #                     item_weight_unit=item_data.get('item_weight_unit', 'kg'),
            #                     item_price=item_data.get('item_price'),
            #                     item_currency=item_data.get('item_currency', 'AUD')
            #                 )
            #                 db.add(item)
                
                db.commit()
                
            except Exception as e:
                print(f"Error processing document {doc_id}: {e}")
                continue
        
        # Update status to 'done'
        if process:
            process.status = ProcessStatus.DONE
            db.commit()
        return {"status": "success", "message": "Documents processed successfully"}
    except Exception as e:
        print(f"Document processing error: {e}")
        # Update status to 'error'
        if process:
            process.status = ProcessStatus.ERROR
            db.commit()
    
    finally:
        db.close()


@celery_app.task
def cleanup_temp_files():
    """Clean up temporary files"""
    from services.file_service import file_service
    cleaned_count = file_service.cleanup_old_files(max_age_hours=24)
    print(f"Cleaned up {cleaned_count} temporary files")
    return cleaned_count


# Import func for database operations
from sqlalchemy.sql import func
