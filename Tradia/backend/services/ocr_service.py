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

    def do_ocr_on_pdf(self, pdf_path: str) -> str:
        """
        Perform OCR on entire PDF document
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            OCR extracted text from all pages
        """
        ocr_text_content = []
        try:
            images = convert_from_path(pdf_path)
            for page_num, img in enumerate(images):
                print(f"Performing OCR on page {page_num + 1}...")
                ocr_text = pytesseract.image_to_string(img, lang="eng")
                ocr_text_content.append(f"=== OCR Page {page_num+1} ===\n{ocr_text.strip()}")
        except Exception as e:
            print(f"OCR conversion error: {e}")
            
        return "\n\n".join(ocr_text_content)

    def ocr_by_page(self, page, page_num):
        """
        Perform OCR on a single page using pdfplumber page object
        
        Args:
            page: pdfplumber page object
            page_num: Page number (0-indexed)
            
        Returns:
            Combined text and OCR content for the page
        """
        text_parts = []
        
        # First, try to extract text directly
        direct_text = page.extract_text() or ""
        text_parts.append(direct_text)
        
        try:
            # Convert page to image and perform OCR
            # Create a temporary image from the page
            bbox = page.bbox
            page_image = page.within_bbox(bbox).to_image(resolution=200)
            
            # Convert to PIL Image for OCR
            pil_image = page_image.original
            ocr_text = pytesseract.image_to_string(pil_image, lang="eng")
            
            # Only add OCR text if it's significantly different from direct text
            if ocr_text.strip() and len(ocr_text.strip()) > len(direct_text.strip()) * 0.5:
                text_parts.append(f"[OCR Text]\n{ocr_text.strip()}")
                
        except Exception as e:
            print(f"OCR error on page {page_num}: {e}")
            # Fallback to fitz-based OCR
            try:
                # Use fitz for OCR as fallback
                doc = fitz.open(page.pdf.stream)
                fitz_page = doc.load_page(page_num)
                mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = fitz_page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Save temporary image
                temp_img_path = f"/tmp/page_{page_num}.png"
                with open(temp_img_path, "wb") as f:
                    f.write(img_data)
                
                # OCR the image
                image = Image.open(temp_img_path)
                ocr_text = pytesseract.image_to_string(image, lang="eng")
                
                if ocr_text.strip():
                    text_parts.append(f"[OCR Text]\n{ocr_text.strip()}")
                
                # Clean up temp file
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
                    
                doc.close()
            except Exception as fallback_error:
                print(f"Fallback OCR error on page {page_num}: {fallback_error}")
        
        return "\n\n".join(text_parts).strip()

    def extract_text_and_tables_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract both text and tables from PDF using pdfplumber with OCR
        
        Returns:
            Dictionary with detailed extraction results including OCR
        """
        results = {
            'text_by_page': [],
            'ocr_by_page': [],
            'tables': [],
            'combined_text': '',
            'combined_ocr': '',
            'formatted_tables': '',
            'page_count': 0,
            'table_count': 0
        }
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                results['page_count'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    print(f"Processing page {page_num + 1} of {len(pdf.pages)}...")
                    
                    # Extract text and OCR from page
                    page_content = self.ocr_by_page(page, page_num)
                    if page_content:
                        results['text_by_page'].append(f"=== Page {page_num+1} ===\n{page_content}")
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
                
                # Perform comprehensive OCR on entire document
                print("Performing comprehensive OCR on entire document...")
                results['full_document_ocr'] = self.do_ocr_on_pdf(pdf_path)
                
        except Exception as e:
            print(f"PDF extraction error: {e}")
            
        return results

    def extract_complete_document_content(self, pdf_path: str) -> str:
        """
        Extract complete document content (text + tables + OCR) formatted for LLM
        
        Returns:
            Complete formatted content ready for LLM prompt with OCR included
        """
        print(f"Starting complete document extraction for: {pdf_path}")
        results = self.extract_text_and_tables_from_pdf(pdf_path)
        
        # Build complete content
        complete_content = []
        
        # Add page-by-page content (includes direct text + OCR)
        if results['combined_text']:
            complete_content.append("=== DOCUMENT TEXT CONTENT (with OCR) ===")
            complete_content.append(results['combined_text'])
            complete_content.append("")
        
        # Add comprehensive OCR results
        if results.get('full_document_ocr'):
            complete_content.append("=== COMPREHENSIVE OCR EXTRACTION ===")
            complete_content.append(results['full_document_ocr'])
            complete_content.append("")
        
        # Add extracted tables
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


# Global instance
ocr_service = OCRService()

# Complete document extraction (text + tables + OCR)
# content = ocr_service.extract_complete_document_content("document.pdf")
# print(content)
# Use directly in your LLM prompt
# prompt = f"Analyze this document:\n\n{content}"

# Get detailed results
# results = ocr_service.extract_text_and_tables_from_pdf("document.pdf")
# tables_only = results['formatted_tables']
# text_only = results['combined_text']