import pandas as pd
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import os
from typing import Optional, List, Dict
from config.settings import settings
import pdfplumber
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
                # PDF file - extract text and tables
                return self._extract_from_pdf_with_tables(file_path)
                
            else:
                # Unsupported format
                return None
                
        except Exception as e:
            print(f"OCR extraction error: {e}")
            return None

    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """
        Extract tables from PDF using pdfplumber
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of pandas DataFrames containing extracted tables
        """
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract tables from current page
                    page_tables = page.extract_tables()
                    
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 1:  # Ensure table has content and headers
                            try:
                                # Convert to DataFrame
                                # Use first row as headers, rest as data
                                headers = table[0]
                                data = table[1:]
                                
                                # Clean headers (remove None, empty strings)
                                clean_headers = []
                                for i, header in enumerate(headers):
                                    if header and str(header).strip():
                                        clean_headers.append(str(header).strip())
                                    else:
                                        clean_headers.append(f"Column_{i+1}")
                                
                                # Create DataFrame
                                df = pd.DataFrame(data, columns=clean_headers)
                                
                                # Clean empty columns and rows
                                df = df.dropna(how='all').dropna(axis=1, how='all')
                                
                                # Remove completely empty cells represented as None
                                df = df.fillna('')
                                
                                if not df.empty and len(df) > 0:
                                    df.name = f"Page_{page_num+1}_Table_{table_num+1}"
                                    tables.append(df)
                                    
                            except Exception as e:
                                print(f"Error processing table on page {page_num+1}, table {table_num+1}: {e}")
                                continue
                                
        except Exception as e:
            print(f"pdfplumber table extraction error: {e}")
            
        return tables

    def format_tables_for_llm(self, tables: List[pd.DataFrame]) -> str:
        """
        Format extracted tables for inclusion in LLM prompt
        
        Args:
            tables: List of pandas DataFrames
            
        Returns:
            Formatted string representation of tables
        """
        if not tables:
            return ""
            
        formatted_tables = []
        
        for i, table in enumerate(tables):
            table_name = getattr(table, 'name', f'Table_{i+1}')
            
            # Create a formatted representation
            table_str = f"\n=== {table_name} ===\n"
            
            # Add table dimensions info
            table_str += f"Dimensions: {table.shape[0]} rows × {table.shape[1]} columns\n\n"
            
            # Convert table to string with better formatting
            # Use to_string for better readability
            table_str += table.to_string(index=False, max_rows=100, max_cols=20)
            table_str += "\n" + "="*60 + "\n"
            
            formatted_tables.append(table_str)
            
        return "\n".join(formatted_tables)

    def extract_text_and_tables_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract both text and tables from PDF using pdfplumber
        
        Returns:
            Dictionary with detailed extraction results
        """
        results = {
            'text_by_page': [],
            'tables': [],
            'combined_text': '',
            'formatted_tables': '',
            'page_count': 0,
            'table_count': 0
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                results['page_count'] = len(pdf.pages)
                for page_num, page in enumerate(pdf.pages):
                    # Extract text from page
                    page_text = self.ocr_by_page(page, page_num, pdf_path=pdf_path)
                    if page_text:
                        results['text_by_page'].append(f"=== Page {page_num+1} ===\n{page_text}")
                    else:
                        results['text_by_page'].append(f"=== Page {page_num+1} ===\n[No extractable text]")
                    


                    # Extract tables from page
                    page_tables = page.extract_tables()
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 1:
                            try:
                                # Process table
                                headers = table[0]
                                data = table[1:]
                                
                                # Clean headers
                                clean_headers = []
                                for i, header in enumerate(headers):
                                    if header and str(header).strip():
                                        clean_headers.append(str(header).strip())
                                    else:
                                        clean_headers.append(f"Column_{i+1}")
                                
                                # Create DataFrame
                                df = pd.DataFrame(data, columns=clean_headers)
                                df = df.dropna(how='all').dropna(axis=1, how='all')
                                df = df.fillna('')
                                
                                if not df.empty:
                                    df.name = f"Page_{page_num+1}_Table_{table_num+1}"
                                    results['tables'].append(df)
                                    
                            except Exception as e:
                                print(f"Error processing table: {e}")
                                continue
                
                # Combine results
                results['combined_text'] = '\n\n'.join(results['text_by_page'])
                results['formatted_tables'] = self.format_tables_for_llm(results['tables'])
                results['table_count'] = len(results['tables'])
                results['ocr_text'] = self.do_ocr_on_pdf(pdf_path)
                
        except Exception as e:
            print(f"PDF extraction error: {e}")
            
        return results

    def extract_complete_document_content(self, pdf_path: str) -> str:
        """
        Extract complete document content (text + tables) formatted for LLM
        
        Returns:
            Complete formatted content ready for LLM prompt
        """
        results = self.extract_text_and_tables_from_pdf(pdf_path)
        
        # Build complete content
        complete_content = []
        
        if results['combined_text']:
            complete_content.append("=== DOCUMENT TEXT CONTENT ===")
            complete_content.append(results['combined_text'])
            complete_content.append("")
        
        if results['formatted_tables']:
            complete_content.append("=== EXTRACTED TABLES ===")
            complete_content.append(results['formatted_tables'])
        
        # Add summary
        summary = f"\n=== DOCUMENT SUMMARY ===\n"
        summary += f"Total Pages: {results['page_count']}\n"
        summary += f"Total Tables Found: {results['table_count']}\n"
        summary += "="*50
        
        complete_content.append(summary)
        
        return "\n".join(complete_content)

    def extract_text_hybrid(self, pdf_path: str) -> Optional[str]:
        """Enhanced hybrid text extraction (original method)"""
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content.append(extracted)
                else:
                    text_content.append("")

        # OCR on every page (for image text)
        ocr_text_content = []
        try:
            images = convert_from_path(pdf_path)
            for img in images:
                ocr_text = pytesseract.image_to_string(img, lang="eng")
                ocr_text_content.append(ocr_text)
        except Exception as e:
            print(f"OCR conversion error: {e}")
            ocr_text_content = [""] * len(text_content)

        # Merge results
        merged_pages = []
        for real_text, ocr_text in zip(text_content, ocr_text_content):
            merged_text = real_text.strip()
            if ocr_text.strip() and ocr_text.strip() not in merged_text:
                merged_text += "\n" + ocr_text.strip()
            merged_pages.append(merged_text)

        return "\n".join(merged_pages)

    def _extract_from_pdf_with_tables(self, pdf_path: str) -> str:
        """Extract text and tables from PDF, return combined content"""
        return self.extract_complete_document_content(pdf_path)

    def _extract_from_pdf(self, pdf_path: str) -> str:
        """Original PDF extraction method (kept for compatibility)"""
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

    def do_ocr_on_pdf(self, pdf_path: str) -> str:
        ocr_text_content = []
        images = convert_from_path(pdf_path)
        for img in images:
            ocr_text = pytesseract.image_to_string(img, lang="eng")
            ocr_text_content.append(ocr_text)
        
        # return ocr_text_content

        # print("OCR Text Content:", ocr_text_content)
        # # 3. Merge results — prefer real text, fallback to OCR
        # merged_pages = []
        # for real_text, ocr_text in zip(text_content, ocr_text_content):
        #     merged_pages.append(real_text.strip() + "\n" + ocr_text.strip())
        return "\n".join(ocr_text_content).strip()

    def ocr_by_page(self, page, page_num, pdf_path=None):
        """
        Extract text from a page using pdfplumber for text, and PyMuPDF for image-based OCR.
        If pdf_path is provided, will use PyMuPDF to render the page for OCR.
        """
        text_parts = []
        # Extract text using pdfplumber
        text_parts.append(page.extract_text() or "")

        # If pdf_path is provided, use PyMuPDF to render the page for OCR
        if pdf_path is not None:
            try:
                import fitz
                doc = fitz.open(pdf_path)
                if page_num < len(doc):
                    mupage = doc.load_page(page_num)
                    mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                    pix = mupage.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    temp_img_path = f"/tmp/page_{page_num}.png"
                    with open(temp_img_path, "wb") as f:
                        f.write(img_data)
                    image = Image.open(temp_img_path)
                    page_text = pytesseract.image_to_string(image)
                    text_parts.append(page_text)
                    os.remove(temp_img_path)
                doc.close()
            except Exception as e:
                print(f"PyMuPDF OCR error on page {page_num+1}: {e}")
        return "\n".join(text_parts).strip()

# Global instance
ocr_service = OCRService()

# # Complete document extraction (text + tables)
content = ocr_service.extract_complete_document_content("document.pdf")
print(content)
# # Use directly in your LLM prompt
# prompt = f"Analyze this document:\n\n{content}"

# # Get detailed results
# results = ocr_service.extract_text_and_tables_from_pdf("document.pdf")
# tables_only = results['formatted_tables']
# text_only = results['combined_text']

# print(results)
