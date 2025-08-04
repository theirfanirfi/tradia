import json
from pathlib import Path
from writeonpdf import get_form_fields_fillpdf

def flatten_json_schema(obj, parent_key='', sep='_'):
    items = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.extend(flatten_json_schema(v, new_key, sep=sep).items())
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            items.extend(flatten_json_schema(item, f"{parent_key}{sep}{idx}", sep=sep).items())
    else:
        items.append((parent_key, obj))
    return dict(items)

if __name__ == "__main__":
    # Get PDF field names
    template_path = "../docs/b650_unlocked.pdf"
    fields_dict = get_form_fields_fillpdf(template_path)
    pdf_fields = set(fields_dict.keys()) if fields_dict else set()
    print(f"PDF fields ({len(pdf_fields)}):", pdf_fields)

    # Load sample schema JSON
    with open("../forms_schema/b650_sample.json") as f:
        sample_data = json.load(f)
    flat_schema = set(flatten_json_schema(sample_data).keys())
    print(f"Schema fields ({len(flat_schema)}):", flat_schema)

    # Compare
    missing_in_pdf = flat_schema - pdf_fields
    missing_in_schema = pdf_fields - flat_schema
    print("\nSchema fields missing in PDF:", missing_in_pdf)
    print("\nPDF fields missing in schema:", missing_in_schema) 