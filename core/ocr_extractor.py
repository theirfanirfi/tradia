import asyncio
from typing import List, Dict, Any
import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd


def df_to_json_prompt(df: pd.DataFrame, orient="records", indent=2) -> str:
    """
    Convert DataFrame to JSON string suitable for embedding in an LLM prompt.
    """
    return df.to_json(orient=orient, indent=indent)

def df_to_structured_text(df: pd.DataFrame) -> str:
    """
    Convert DataFrame to structured text representation.
    Each row becomes a line with key: value pairs.
    """
    lines = []
    for _, row in df.iterrows():
        pairs = [f"{col}: {row[col]}" for col in df.columns]
        lines.append(", ".join(pairs))
    return "\n".join(lines)

async def extract_text_from_file(path: str) -> str:
    """
    Extract all text from a PDF or image file.
    For PDFs: Uses pdfplumber for text and table extraction
    For images: Uses Tesseract OCR
    Returns the concatenated plaintext with tables formatted as text.
    """
    # Use run_in_executor so we don't block the event loop
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_extract, path)


def _sync_extract(path: str) -> str:
    """
    Synchronous extraction function called within a thread pool.
    """
    text_chunks: List[str] = []

    if path.lower().endswith((".png", ".jpg", ".jpeg", ".tiff")):
        # Single-image OCR
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        text_chunks.append(text)

    elif path.lower().endswith(".pdf"):
        # Use pdfplumber for PDF text and table extraction
        try:
            with pdfplumber.open(path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = f"\n--- Page {page_num} ---\n"
                    
                    # Extract text
                    text = page.extract_text()
                    if text:
                        page_text += f"\nText Content:\n{text}\n"
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        page_text += f"\nTables Found: {len(tables)}\n"
                        for table_num, table in enumerate(tables, 1):
                            if table and len(table) > 0:
                                # Convert table to DataFrame for better formatting
                                df = pd.DataFrame(table[1:], columns=table[0])
                                # page_text += f"\nTable {table_num}:\n{df.to_string(index=False)}\n"
                                page_text += f"\nTable {table_num}:\n{df_to_structured_text(df)}\n"
                    
                    text_chunks.append(page_text)
                    
        except Exception as e:
            # Fallback to OCR if pdfplumber fails (e.g., scanned PDF)
            try:
                from pdf2image import convert_from_path
                pages = convert_from_path(path, dpi=300)
                for page in pages:
                    text_chunks.append(pytesseract.image_to_string(page))
            except Exception as ocr_error:
                raise ValueError(f"Failed to extract text from PDF {path}: {e}. OCR fallback also failed: {ocr_error}")

    else:
        raise ValueError(f"Unsupported file type for extraction: {path}")

    # Join with page breaks
    return "\n\n".join(text_chunks)


def extract_tables_from_pdf(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extract only tables from a PDF file using pdfplumber.
    Returns a list of pandas DataFrames.
    """
    dfs = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 0:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        dfs.append(df)
        return dfs
    except Exception as e:
        raise ValueError(f"Error extracting tables from {pdf_path}: {e}")


def extract_text_and_tables_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extract both text and tables from a PDF file.
    Returns a dictionary with 'text' and 'tables' keys.
    """
    result = {"text": "", "tables": []}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_chunks = []
            for page in pdf.pages:
                # Extract text
                text = page.extract_text()
                if text:
                    text_chunks.append(text)
                
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 0:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        result["tables"].append(df)
            
            result["text"] = "\n\n".join(text_chunks)
            
    except Exception as e:
        raise ValueError(f"Error extracting from {pdf_path}: {e}")
    
    return result
