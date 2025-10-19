from typing import Dict, Any, Optional
import logging
from models import UserProcessItem, UserDocument
from sqlalchemy.orm import Session
from config.settings import settings
from prompts.Item_extraction_prompt import get_items_extraction_prompt
from prompts.B650_section_a_extraction_prompt import get_b650_section_a_extraction_prompt
from prompts.B650_section_b_sea_extraction_prompt import get_b650_section_b_sea_extraction_prompt
from prompts.B650_section_c_extraction_prompt import get_b650_section_c_extraction_prompt

class PreLLMService:
    """Service that handles all pre-LLM processing and prompt preparation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def prepare_process_documents(process_id: str, document_ids: List[str]):
        pass

    async def prepare_items_extraction(self, document_id:str, db:Session):
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
                return False, {"status": "error", "message": "No OCR text found"}
            
            declaration_type = "import"
            
            prompt_template = get_items_extraction_prompt(ocr_text, declaration_type)
            prompt = prompt_template.format(
                ocr_text=ocr_text, declaration_type=declaration_type
            )
            return True, {
                "prompt": prompt,
                "document_id": document.document_id,
                "process_id": process_id
            }

        except Exception as e:
            return False, {"status": "error", "message": "Prompt forumulation error"}
            self.logger.error(f"Error preparing item extraction: {str(e)}")
            raise


    async def prepare_item_extraction(
        self, 
        item_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Prepare data for item extraction"""
        try:
            item = db.query(UserProcessItem).filter(
                UserProcessItem.item_id == item_id
            ).first()
            
            if not item:
                raise ValueError(f"Item {item_id} not found")
                
            # Get associated document
            document = db.query(UserDocument).filter(
                UserDocument.document_id == item.document_id
            ).first()
            
            if not document or not document.ocr_text:
                raise ValueError(f"No OCR text found for document {item.document_id}")

            # Format prompt with OCR text
            prompt = get_items_extraction_prompt(
                ocr_text=document.ocr_text,
                declaration_type="import"  # or get from document type
            )
            
            return {
                "prompt": prompt,
                "item_id": item_id,
                "document_id": document.document_id,
                "process_id": item.process_id
            }

        except Exception as e:
            self.logger.error(f"Error preparing item extraction: {str(e)}")
            raise

    async def prepare_section_a_extraction(
        self,
        document_id: str, 
        db: Session
    ) -> Dict[str, Any]:
        """Prepare data for B650 Section A extraction"""
        try:
            document = db.query(UserDocument).filter(
                UserDocument.document_id == document_id
            ).first()
            
            if not document or not document.ocr_text:
                raise ValueError(f"No OCR text found for document {document_id}")

            prompt = get_b650_section_a_extraction_prompt(
                ocr_text=document.ocr_text
            )

            return {
                "prompt": prompt,
                "document_id": document_id,
                "process_id": document.process_id
            }

        except Exception as e:
            self.logger.error(f"Error preparing section A extraction: {str(e)}")
            raise

    async def prepare_section_b_extraction(
        self,
        document_id: str,
        mode_of_transport: str,
        db: Session
    ) -> Dict[str, Any]:
        """Prepare data for B650 Section B extraction"""
        try:
            document = db.query(UserDocument).filter(
                UserDocument.document_id == document_id
            ).first()
            
            if not document or not document.ocr_text:
                raise ValueError(f"No OCR text found for document {document_id}")

            prompt = get_b650_section_b_sea_extraction_prompt(
                ocr_text=document.ocr_text,
                mode_of_transport=mode_of_transport
            )

            return {
                "prompt": prompt,
                "document_id": document_id,
                "process_id": document.process_id,
                "mode_of_transport": mode_of_transport
            }

        except Exception as e:
            self.logger.error(f"Error preparing section B extraction: {str(e)}")
            raise

    async def prepare_section_c_extraction(
        self,
        document_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Prepare data for B650 Section C extraction"""
        try:
            document = db.query(UserDocument).filter(
                UserDocument.document_id == document_id
            ).first()
            
            if not document or not document.ocr_text:
                raise ValueError(f"No OCR text found for document {document_id}")

            prompt = get_b650_section_c_extraction_prompt(
                ocr_text=document.ocr_text
            )

            return {
                "prompt": prompt,
                "document_id": document_id,
                "process_id": document.process_id
            }

        except Exception as e:
            self.logger.error(f"Error preparing section C extraction: {str(e)}")
            raise

# Global instance
pre_llm_service = PreLLMService()