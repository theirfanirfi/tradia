from anyio import sleep
from celery import Celery
from typing import List
import json
from config.settings import settings
from services.ocr_service import ocr_service
# from services.llm_service import llm_service
from services.OpenAIService import openai_llm_service as llm_service
# from services.TariffClassifier import catalog
from models import UserDocument, UserProcessItem, UserProcess, ProcessStatus
from config.database import SessionLocal
from sqlalchemy.orm import Session
from celery.utils.log import get_task_logger
from utils.regex import get_numbers
from llm_response_formats.items_extraction_format import RESPONSE_FORMAT
from services.PreLLMB650 import pipeline, convert_result_to_json
from schemas.B650.import_section_a import B650SectionAHeader
from schemas.B650.import_section_b_sea import SeaTransportLine
from schemas.B650.import_section_c_schema import SECTIONC
from models.user_declaration import UserDeclaration
from services.B650_PreLLMService import preprocessor


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
    process = None
    
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
                ocr_text = ocr_service.extract_complete_document_content(document.file_path)
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
                    "import",  # Default to import, can be enhanced
                    response_format=RESPONSE_FORMAT
                )
                print(f"LLM response: {llm_response}")
                
                if llm_response:
                    document.llm_response = llm_response
                    document.processed_at = db.query(func.now()).scalar()
                    process.status = ProcessStatus.EXTRACTING
                    db.commit()
                    
                    
                    # Extract items from LLM response
                    if 'items' in llm_response:
                        for item_data in llm_response['items']:
                            item = UserProcessItem(
                                process_id=process_id,
                                document_id=document.document_id,
                                item_title=item_data.get('item_title', 'Unknown Item'),
                                item_description=item_data.get('item_description'),
                                item_type=item_data.get('item_type'),
                                item_weight=get_numbers(item_data.get('item_weight')),
                                item_weight_unit=item_data.get('item_weight_unit', 'kg'),
                                item_price=get_numbers(item_data.get('item_price')),
                                item_currency=item_data.get('item_currency', 'AUD'),
                                # item_hs_code=catalog.predict_best(item_data.get('item_title', ''))[0].code if item_data.get('item_title') else None
                                item_hs_code="1234"
                            )
                            db.add(item)
                
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

@celery_app.task
def task_retry_item_extraction_from_document(document_id: str):
    """Background task to retry item extraction for a single document."""
    db = SessionLocal()
    try:
        document = db.query(UserDocument).filter(UserDocument.document_id == document_id).first()
        if not document:
            print(f"Document {document_id} not found for retry.")
            return {"status": "error", "message": "Document not found"}

        process_id = document.process_id
        # process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        # if process:
        #     process.status = ProcessStatus.EXTRACTING
        #     db.commit()

        # Use the latest OCR text
        ocr_text = document.ocr_text
        if not ocr_text:
            print(f"No OCR text for document {document_id}.")
            return {"status": "error", "message": "No OCR text found"}

        # LLM processing
        llm_response = llm_service.process_item_extract_document(
            ocr_text,
            process_id,
            "import",  # Default to import, can be enhanced
            response_format=RESPONSE_FORMAT
        )
        print(f"LLM response (retry): {llm_response}")

        if llm_response:
            document.llm_response = llm_response
            document.processed_at = db.query(func.now()).scalar()
            # process.status = ProcessStatus.EXTRACTING
            db.commit()

            # Remove old items for this document
            db.query(UserProcessItem).filter(UserProcessItem.document_id == document_id).delete()
            db.commit()

            # Extract items from LLM response
            if 'items' in llm_response:
                for item_data in llm_response['items']:
                    item = UserProcessItem(
                        process_id=process_id,
                        document_id=document.document_id,
                        item_title=item_data.get('item_title', 'Unknown Item'),
                        item_description=item_data.get('item_description'),
                        item_type=item_data.get('item_type'),
                        item_weight=get_numbers(item_data.get('item_weight')),
                        item_weight_unit=item_data.get('item_weight_unit', 'kg'),
                        item_price=get_numbers(item_data.get('item_price')),
                        item_currency=item_data.get('item_currency', 'AUD'),
                        item_hs_code="1234"
                        # item_hs_code=catalog.predict_best(item_data.get('item_title', ''))[0].code if item_data.get('item_title') else None
                    )
                    db.add(item)
            db.commit()

        # if process:
        #     process.status = ProcessStatus.DONE
        #     db.commit()
        return {"status": "success", "message": "Retry extraction completed"}
    except Exception as e:
        print(f"Retry extraction error: {e}")
        # if process:
        #     process.status = ProcessStatus.ERROR
        #     db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


#task for reclassifying items using TariffClassifier
@celery_app.task
def task_reclassify_items(item_id: str = None):
    """Background task to reclassify items using TariffClassifier"""
    db = SessionLocal()
    print('reclassifying items task')
    try:
        item = db.query(UserProcessItem).filter(UserProcessItem.item_id == item_id).first()
        if item:
            if item.item_title:
                item.item_hs_code = "1234"
                # predicted = catalog.predict_best(item.item_title)
                # if predicted:
                #     print('predicted:', predicted[0].code)
                #     item.item_hs_code = predicted[0].code
        db.commit()

        return True, {"status": "success", "message": f"Reclassified items."}
    except Exception as e:
        print(f"Reclassification error: {e}")
        return False, {"status": "error", "message": str(e)}
    finally:
        db.close()


#task for reclassifying items using TariffClassifier
@celery_app.task
def task_b650_extract_section_a_information(process_id: str = None):
    """Background task to extract b650 section a information"""
    db = SessionLocal()
    print('extracting section a task')
    try:
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if not process:
            return False, {"status": "error"}
    
        documents = db.query(UserDocument).filter(UserDocument.process_id == process_id).all()
        if not documents:
            return False, {"status": "error", "message": "No document found"}
        
        text = ""
        for doc in documents:
            text += str(doc.ocr_text)
        
        # # Process text
        result = pipeline.process(text)

        
        user_declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
        if not user_declaration:
            user_declaration = UserDeclaration()

        # # llm._call()

        # # Convert to JSON
        json_result = convert_result_to_json(result)
        # print(json_result)

        parsed = llm_service.process_b650_section_a(ocr_text=text, structured_data=json_result)
        if parsed:
            header = parsed["header"]
            section_a = B650SectionAHeader(**header)
            json_str = section_a.model_dump(exclude_none=False, mode='json')
            # user_declaration = UserDeclaration()
            user_declaration.declaration_type = "import"
            user_declaration.import_declaration_section_a = json_str
            user_declaration.process_id = process_id
            db.add(user_declaration)
            db.commit()

        # db.commit()
        task_b650_extract_section_b_information.delay(process_id)

        return True, {"status": "success", "message": f"Reclassified items."}
    except Exception as e:
        print(f"B650 Section a extraction error: {e}")
        return False, {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task
def task_b650_extract_section_b_information(process_id: str = None):
    """Background task to extract b650 section B information"""
    db = SessionLocal()
    print('extracting section b task')
    try:
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if not process:
            return False, {"status": "error"}
    
        documents = db.query(UserDocument).filter(UserDocument.process_id == process_id).all()
        if not documents:
            return False, {"status": "error", "message": "No document found"}
        
        text = ""
        for doc in documents:
            text += str(doc.ocr_text)
        
        # # Process text
        result = pipeline.process(text)
        resultt = preprocessor.process(text)

        b650_structure = preprocessor.to_b650_structure(resultt)
        section_b = b650_structure["section_b_transport_details"]
        print(f"Mode of Transport: {section_b['mode_of_transport']}")
        mode_of_transport = section_b['mode_of_transport']
        # print(section_b)
        # logger.info(section_b)
    
        
        user_declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
        if not user_declaration:
            user_declaration = UserDeclaration()

        # # # llm._call()

        # # # Convert to JSON
        json_result = convert_result_to_json(result)
        # # print(json_result)

        parsed = llm_service.process_b650_section_b(ocr_text=text, structured_data=json_result, mode_of_transport=mode_of_transport)
        if parsed:
            section_b = None
            if mode_of_transport == "SEA":
                sea_transport_lines = parsed["sea_transport_lines"]
                section_b = SeaTransportLine(**sea_transport_lines)
            elif mode_of_transport == "AIR":
                pass

            json_str = section_b.model_dump(exclude_none=False, mode='json')
            # user_declaration = UserDeclaration()
            user_declaration.declaration_type = "import"
            user_declaration.import_declaration_section_b = json_str
            user_declaration.process_id = process_id
            db.add(user_declaration)
            db.commit()

        # # db.commit()
        task_b650_extract_section_c_information.delay(process_id)

        return True, {"status": "success", "message": f"Section B extracted."}
    except Exception as e:
        print(f"B650 Section b extraction error: {e}")
        return False, {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task
def task_b650_extract_section_c_information(process_id: str = None):
    """Background task to extract b650 section c information"""
    db = SessionLocal()
    print('extracting section c task')
    try:
        process = db.query(UserProcess).filter(UserProcess.process_id == process_id).first()
        if not process:
            return False, {"status": "error"}
    
        documents = db.query(UserDocument).filter(UserDocument.process_id == process_id).all()
        if not documents:
            return False, {"status": "error", "message": "No document found"}
        
        text = ""
        for doc in documents:
            text += str(doc.ocr_text)
        
        # # Process text
        result = pipeline.process(text)

        # print(section_b)
        # logger.info(section_b)
    
        
        user_declaration = db.query(UserDeclaration).filter(UserDeclaration.process_id == process_id).first()
        if not user_declaration:
            return False

        # # # llm._call()

        # # # Convert to JSON
        json_result = convert_result_to_json(result)
        section_c = user_declaration.import_declaration_section_c
        # # print(json_result)

        parsed = llm_service.process_b650_section_c(ocr_text=section_c, structured_data=json_result)
        if parsed:
            print(parsed)
            tariff_lines = parsed["tariff_lines"]
            section_c = SECTIONC(**tariff_lines)

            json_str = section_c.model_dump(exclude_none=False, mode='json')
            # user_declaration = UserDeclaration()
            user_declaration.declaration_type = "import"
            user_declaration.import_declaration_section_c = json_str
            user_declaration.process_id = process_id
            db.add(user_declaration)
            db.commit()

        # # db.commit()

        return True, {"status": "success", "message": f"Section B extracted."}
    except Exception as e:
        print(f"B650 Section c extraction error: {e}")
        return False, {"status": "error", "message": str(e)}
    finally:
        db.close()