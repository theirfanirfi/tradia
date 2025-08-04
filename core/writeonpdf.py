#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from fillpdf import fillpdfs

def list_fields(template_path: Path):
    """Return a dict of {field_name: field_type} from the PDF."""
    return fillpdfs.get_form_fields(str(template_path))

def extract_value(data: dict, path: str):
    """
    Given nested JSON `data` and a dot-delimited `path`, return the string value
    or empty string if missing.
    """
    cur = data
    for key in path.split('.'):
        if isinstance(cur, list):
            try:
                idx = int(key)
                cur = cur[idx]
            except:
                return ""
        elif isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return ""
    return "" if cur is None else str(cur)

def build_flat_data(llm_json: dict, schema_map: dict):
    """
    Build { pdf_field_name: value } from your LLM JSON and mapping.
    schema_map maps "schema.key.path" → "PDF Field Name".
    """
    flat = {}
    for schema_path, pdf_field in schema_map.items():
        flat[pdf_field] = extract_value(llm_json, schema_path)
    return flat

def fill_pdf_resilient(template_path: Path, output_path: Path, flat_data: dict):
    """
    Try filling one field at a time.  On success, lock it in; on failure, skip it.
    Returns a dict of { field_name: error_message } for the ones that failed.
    """
    successes = {}
    errors = {}

    # iterate through each field/value
    for field, value in flat_data.items():
        trial = {**successes, field: value}
        try:
            fillpdfs.write_fillable_pdf(
                str(template_path),
                str(output_path),
                trial
            )
            # if we got here, this field worked—lock it in
            successes[field] = value
        except Exception as e:
            errors[field] = str(e)
            # continue on to the next field

    # final write to make sure all successes are in the output
    # (in case the last trial was a failure)
    if successes:
        fillpdfs.write_fillable_pdf(
            str(template_path),
            str(output_path),
            successes
        )

    return errors

def main():
    args = sys.argv[1:]
    if len(args) == 4:
        tpl_path, data_path, map_path, out_path = map(Path, args)  
        print(f"  template: {tpl_path}")
        print(f"  data    : {data_path}")
        print(f"  mapping : {map_path}")
        print(f"  output  : {out_path}\n")
    else:
        print("Usage:\n  python pdf_fillpdf_mapped.py "
              "<template.pdf> <llm_data.json> <schema_to_pdf_map.json> <output.pdf>")
        sys.exit(1)

    # Load LLM JSON
    try:
        llm_json = json.loads(data_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading LLM data JSON ({data_path}): {e}")
        sys.exit(1)

    # Load schema→PDF mapping
    try:
        schema_map = json.loads(map_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading mapping JSON ({map_path}): {e}")
        sys.exit(1)

    # Show PDF fields
    print(f"PDF fields in template ({tpl_path}):")
    for name, ftype in list_fields(tpl_path).items():
        print(f"  - {name} ({ftype})")

    # Build flat data dict
    flat_data = build_flat_data(llm_json, schema_map)

    # Warn about any PDF fields left blank
    blanks = [f for f, v in flat_data.items() if not v]
    if blanks:
        print("\nWarning: these PDF fields will be blank:")
        for f in blanks:
            print(f"  - {f}")

    # Fill & write, but resilient to per-field errors
    print("\nFilling PDF…")
    errors = fill_pdf_resilient(tpl_path, out_path, flat_data)

    if errors:
        print("\nWarning: could not fill these PDF fields:")
        for f, msg in errors.items():
            print(f"  - {f}: {msg}")

    print(f"\nDone!  Saved to {out_path}")

if __name__ == "__main__":
    main()
