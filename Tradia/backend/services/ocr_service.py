import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import os
from typing import Optional
from config.settings import settings
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import re


class OCRService:
    def __init__(self):
        self.engine = settings.ocr_engine
        
    def extract_text(self, file_path: str) -> Optional[str]:
        """Extract text from document using OCR"""
        try:
            if not os.path.exists(file_path):
                return None
                
            # Get file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Image file - use PIL + Tesseract
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                return text.strip()
                
            elif file_ext == '.pdf':
                # PDF file - convert to image then OCR
                return self._extract_from_pdf(file_path)
                
            else:
                # Unsupported format
                return None
                
        except Exception as e:
            print(f"OCR extraction error: {e}")
            return None
    
    def extract_text_hybrid(self, pdf_path: str) -> Optional[str]:
    # 1. Try to extract selectable text
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                # print(extracted)
                if extracted:
                    text_content.append(extracted)
                else:
                    text_content.append("")  # Keep alignment

        print("Text Content:", text_content)
        # 2. OCR on every page (for image text)
        ocr_text_content = []
        images = convert_from_path(pdf_path)
        for img in images:
            ocr_text = pytesseract.image_to_string(img, lang="eng")
            ocr_text_content.append(ocr_text)
        
        return ocr_text_content

        print("OCR Text Content:", ocr_text_content)
        # 3. Merge results — prefer real text, fallback to OCR
        merged_pages = []
        for real_text, ocr_text in zip(text_content, ocr_text_content):
            merged_pages.append(real_text.strip() + "\n" + ocr_text.strip())

        return "\n".join(merged_pages)

    
    def _extract_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF by converting pages to images"""
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Try to extract text directly first
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
                    continue
                
                # If no text, convert to image and OCR
                mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Save temporary image
                temp_img_path = f"/tmp/page_{page_num}.png"
                with open(temp_img_path, "wb") as f:
                    f.write(img_data)
                
                # OCR the image
                image = Image.open(temp_img_path)
                page_text = pytesseract.image_to_string(image)
                text_parts.append(page_text)
                
                # Clean up temp file
                os.remove(temp_img_path)
            
            doc.close()
            return "\n".join(text_parts).strip()
            
        except Exception as e:
            print(f"PDF OCR error: {e}")
            return ""


# Global instance
ocr_service = OCRService()
