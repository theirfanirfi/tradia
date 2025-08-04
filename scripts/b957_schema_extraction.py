#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from pypdf import PdfReader
from pypdf.errors import PdfReadError

def extract_pdf_schema(pdf_path: Path) -> dict:
    """
    Reads the PDF form at `pdf_path` and returns a dict
    { field_name: "" } for every form field it finds via /AcroForm.
    """
    reader = PdfReader(str(pdf_path))
    acro = reader.trailer.get("/AcroForm")
    if not acro:
        raise PdfReadError("No AcroForm found in PDF")
    fields = reader.get_fields() or {}
    return { name: "" for name in fields.keys() }

def main():
    # Hardcoded paths – adjust these if your files live elsewhere
    pdf_path    = Path("/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/scripts/b957_unlocked_1_.pdf")
    schema_path = Path("b957_pdf_schema.json")

    if not pdf_path.is_file():
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    schema_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        schema = extract_pdf_schema(pdf_path)
        if not schema:
            print("Warning: No form fields found—are you sure this is a fillable PDF?")
        schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(f"Wrote {len(schema)} fields to {schema_path}")
    except PdfReadError as e:
        print(f"Error reading PDF form: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
