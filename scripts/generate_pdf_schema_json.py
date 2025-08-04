#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Make sure fillpdf is installed
try:
    from fillpdf import fillpdfs
except ModuleNotFoundError:
    print("Error: The 'fillpdf' package is not installed.")
    print("Please install it with:\n    pip install fillpdf")
    sys.exit(1)

def extract_pdf_schema(pdf_path: Path) -> dict:
    """
    Reads the PDF form at `pdf_path` and returns a dict
    { field_name: "" } for every form field.
    """
    fields = fillpdfs.get_form_fields(str(pdf_path))
    return { name: "" for name in fields.keys() }

def main():
    # Hardcoded default paths
    pdf_path    = Path("/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/scripts/b957_unlocked.pdf")
    schema_path = Path("/home/abdulwahab-bhai/personal/tradia_ai_backend/backend/forms_schema/b957_pdf_schema.json")

    # Ensure input exists
    if not pdf_path.is_file():
        print(f"Error: PDF not found at {pdf_path}")
        sys.exit(1)

    # Ensure output directory exists
    schema_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract & write
    try:
        schema = extract_pdf_schema(pdf_path)
        schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        print(f"Wrote {len(schema)} fields to {schema_path}")
    except Exception as e:
        print(f"Failed to extract schema from {pdf_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
