# extract_compare.py
# Python script to test multiple PDF extraction methods and save outputs to a single text file.

# Install dependencies in your environment (not here):
# pip install camelot-py tabula-py pdfplumber pymupdf pandas langchain unstructured

import camelot
import tabula
import pdfplumber
import fitz  # PyMuPDF
import pandas as pd
import os
from langchain.document_loaders import UnstructuredPDFLoader

OUTPUT_FILE = "extraction_output.txt"

# Unified extractors returning (error_msg, data)

def extract_camelot(pdf_path, pages="1-end"):
    """Extract tables using Camelot; returns (error, list_of_dfs)."""
    try:
        tables = camelot.read_pdf(pdf_path, pages=pages, flavor="lattice")
        dfs = [table.df for table in tables]
        return None, dfs
    except Exception as e:
        return f"[Camelot] Error extracting {pdf_path}: {e}", []


def extract_tabula(pdf_path, pages="all"):
    """Extract tables using Tabula-py; returns (error, list_of_dfs)."""
    try:
        dfs = tabula.read_pdf(pdf_path, pages=pages, lattice=True)
        return None, dfs
    except Exception as e:
        return f"[Tabula-py] Error extracting {pdf_path}: {e}", []


def extract_pdfplumber(pdf_path):
    """Extract tables using pdfplumber; returns (error, list_of_dfs)."""
    dfs = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    dfs.append(df)
        return None, dfs
    except Exception as e:
        return f"[pdfplumber] Error extracting {pdf_path}: {e}", []


def extract_pymupdf(pdf_path):
    """Extract raw text using PyMuPDF; returns (error, text)."""
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        return None, text
    except Exception as e:
        return f"[PyMuPDF] Error extracting {pdf_path}: {e}", ""


def extract_unstructured_langchain(pdf_path):
    """Extract text using LangChain's UnstructuredPDFLoader; returns (error, text)."""
    try:
        loader = UnstructuredPDFLoader(pdf_path)
        docs = loader.load()
        # Concatenate page contents
        text = "\n".join([doc.page_content for doc in docs])
        return None, text
    except Exception as e:
        return f"[UnstructuredLoader] Error extracting {pdf_path}: {e}", ""

if __name__ == "__main__":
    # List your PDF files here to test
    pdf_paths = [
        "invoice.pdf",
        "packing_list.pdf",
        # Add more file paths as needed
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_file:
        for pdf in pdf_paths:
            out_file.write(f"=== Processing {pdf} ===\n")

            if not os.path.exists(pdf):
                out_file.write(f"File not found: {pdf}\n\n")
                continue

            # Camelot
            err, camelot_tables = extract_camelot(pdf)
            if err:
                out_file.write(err + "\n")
            out_file.write(f"[Camelot] Found {len(camelot_tables)} tables.\n")
            for i, df in enumerate(camelot_tables, start=1):
                out_file.write(f"-- Table {i} (Camelot) --\n")
                out_file.write(df.to_string(index=False) + "\n")

            # Tabula-py
            err, tabula_tables = extract_tabula(pdf)
            if err:
                out_file.write(err + "\n")
            out_file.write(f"[Tabula-py] Found {len(tabula_tables)} tables.\n")
            for i, df in enumerate(tabula_tables, start=1):
                out_file.write(f"-- Table {i} (Tabula-py) --\n")
                out_file.write(df.to_string(index=False) + "\n")

            # pdfplumber
            err, pdfplumber_tables = extract_pdfplumber(pdf)
            if err:
                out_file.write(err + "\n")
            out_file.write(f"[pdfplumber] Found {len(pdfplumber_tables)} tables.\n")
            for i, df in enumerate(pdfplumber_tables, start=1):
                out_file.write(f"-- Table {i} (pdfplumber) --\n")
                out_file.write(df.to_string(index=False) + "\n")

            # PyMuPDF
            err, raw_text = extract_pymupdf(pdf)
            if err:
                out_file.write(err + "\n")
            else:
                preview = raw_text[:1000].replace('\n', ' ')
                out_file.write("[PyMuPDF] Extracted text preview (first 1000 chars):\n")
                out_file.write(preview + "\n")

            # Unstructured via LangChain
            err, lc_text = extract_unstructured_langchain(pdf)
            if err:
                out_file.write(err + "\n")
            else:
                preview = lc_text[:1000].replace('\n', ' ')
                out_file.write("[UnstructuredLoader] Extracted text preview (first 1000 chars):\n")
                out_file.write(preview + "\n")

            out_file.write("\n")

    print(f"Extraction complete. Outputs saved to {OUTPUT_FILE}")
