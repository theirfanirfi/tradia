def map_b650_to_formdata(b650_json):
    """
    Safely converts a JSON object (B650_RESPONSE_FORMAT) into a flat dictionary (form_data)
    used to fill the B650 PDF form.
    Missing fields are filled with empty strings, and missing keys are logged.
    """

    form_data = {}

    def safe_get(container, key, context=""):
        """Safe getter that logs if data is missing."""
        value = ""
        if isinstance(container, dict):
            value = container.get(key, "")
            if value in (None, ""):
                print(f"[INFO] Missing or empty: {context}.{key}")
        else:
            print(f"[INFO] Invalid container for {context}.{key}")
        return value

    header = b650_json.get("header", {})
    air_lines = b650_json.get("air_transport_lines", [])
    sea_lines = b650_json.get("sea_transport_lines", [])
    tariff_lines = b650_json.get("tariff_lines", [])

    # --- HEADER ---
    form_data.update({
        "Import type": safe_get(header, "import_declaration_type", "header"),
        "Owner Details Owner Name": safe_get(header, "owner_name", "header"),
        "Owner ID ABN ABNCAC or CCID": safe_get(header, "owner_id", "header"),
        "Owner Reference": safe_get(header, "owner_reference", "header"),
        "Biosecurity Inspection Location": safe_get(header, "aqis_inspection_location", "header"),
        "Owner email": safe_get(header, "contact_details", "header"),
        "Destination Port Code": safe_get(header, "destination_port_code", "header"),
        "Invoice Term Type": safe_get(header, "invoice_term_type", "header"),
        "Valuation Date": safe_get(header, "valuation_date", "header"),
        "Header Valuation Advice No": safe_get(header, "header_valuation_advice_number", "header"),
        "EFT": safe_get(header, "paid_under_protest", "header"),
        "T3": safe_get(header, "amber_statement_reason", "header"),
        "Declaration": safe_get(header, "declaration_signature", "header")
    })

    # Valuation elements → split into Amount/Currency pairs
    valuation_elements = safe_get(header, "valuation_elements", "header")
    if valuation_elements:
        pairs = valuation_elements.split(",")
        for i, pair in enumerate(pairs, 1):
            parts = pair.strip().split()
            if len(parts) == 2:
                form_data[f"Amount{i}"], form_data[f"Currency{i}"] = parts
            elif len(parts) == 1:
                form_data[f"Amount{i}"] = parts[0]
            else:
                print(f"[INFO] Could not parse valuation element '{pair}'")

    # --- AIR TRANSPORT LINES ---
    for i, line in enumerate(air_lines, start=1):
        context = f"air_transport_lines[{i}]"
        form_data.update({
            "Airline Code": safe_get(line, "airline_code", context),
            f"Loading Port{i}": safe_get(line, "loading_port", context),
            f"First Arrival Port{i}": safe_get(line, "first_arrival_port", context),
            "Discaharge Port1": safe_get(line, "discharge_port", context),
            f"First Arrival Date{i}": safe_get(line, "first_arrival_date", context),
            f"Gross Weight{i}": safe_get(line, "gross_weight", context),
            f"Gross Weight Unit{i}": safe_get(line, "gross_weight_unit", context),
            f"Line No{i}": safe_get(line, "line_number", context),
            f"Master Air Waybill NoRow{i}": safe_get(line, "master_air_waybill_no", context),
            f"House Air Waybill NoRow{i}": safe_get(line, "house_air_waybill_no", context),
            f"No of Packages{i}": safe_get(line, "number_of_packages", context),
            f"Marks  Numbers DescriptionRow{i}": safe_get(line, "marks_numbers_description", context)
        })

    # --- SEA TRANSPORT LINES ---
    for idx, line in enumerate(sea_lines, start=1):
        suffix = ["", "_2", "_3", "_4"][idx - 1] if idx <= 4 else f"_{idx}"
        context = f"sea_transport_lines[{idx}]"
        form_data.update({
            "Vessel Name": safe_get(line, "vessel_name", context),
            "Vessel ID": safe_get(line, "vessel_id", context),
            "Voyage No": safe_get(line, "voyage_number", context),
            f"Loading Port{suffix}": safe_get(line, "loading_port", context),
            f"First arrival{idx}": safe_get(line, "first_arrival_port", context),
            f"Discharge Port{suffix}": safe_get(line, "discharge_port", context),
            f"First Arrival Date{suffix}": safe_get(line, "first_arrival_date", context),
            f"Gross Weight{suffix}": safe_get(line, "gross_weight", context),
            f"Gross Weight Unit{suffix}": safe_get(line, "gross_weight_unit", context),
            f"Line No{idx+2}": safe_get(line, "line_number", context),
            f"Cargo TypeRow{idx}": safe_get(line, "cargo_type", context),
            f"Container NoRow{idx}": safe_get(line, "container_number", context),
            f"Ocean Bill of Lading No{idx}": safe_get(line, "ocean_bill_of_lading_no", context),
            f"House Bill of Lading No{idx}": safe_get(line, "house_bill_of_lading_no", context),
            f"No of Packages{idx+2}": safe_get(line, "number_of_packages", context),
            f"Marks  Numbers DescriptionRow{idx+2}": safe_get(line, "marks_numbers_description", context)
        })

    # --- TARIFF LINES ---
    for i, line in enumerate(tariff_lines, start=1):
        suffix = "" if i == 1 else "_2"
        context = f"tariff_lines[{i}]"
        form_data.update({
            f"Tariff Classification No{suffix}": safe_get(line, "tariff_classification", context),
            f"Goods DescriptionC{suffix}": safe_get(line, "goods_description", context),
            f"Quantity1{suffix}": str(safe_get(line, "quantity", context)),
            f"Unit1{suffix}": safe_get(line, "unit_of_measure", context),
            f"Origin Country1{suffix}": safe_get(line, "country_of_origin", context),
            f"AmountC1{suffix}": safe_get(line, "customs_value", context),
            f"PriceRow1{suffix}": safe_get(line, "fob_value", context),
            f"PriceRow2{suffix}": safe_get(line, "cif_value", context),
            f"Preference Origin Country1{suffix}": safe_get(line, "origin_country_code", context),
            f"Preference Rule Type1{suffix}": safe_get(line, "preference_rule_type", context),
            f"Preference Scheme Type1{suffix}": safe_get(line, "preference_scheme_type", context),
            f"Instrument Type1{suffix}": safe_get(line, "tariff_instrument", context),
            f"Additional Information{suffix}": safe_get(line, "additional_information", context),
            f"Stat code1{suffix}": safe_get(line, "tariff_classification_code", context)
        })

    print("[INFO] Mapping completed successfully.")
    return form_data


# Example usage
# if __name__ == "__main__":
#     from pprint import pprint

#     # Example incomplete B650 JSON (some fields missing intentionally)
#     b650_sample = {
#         "header": {
#             "import_declaration_type": "s71A",
#             "owner_name": "Jane Smith",
#             "invoice_term_type": "CIF",
#             # Missing many fields to demonstrate logging
#         },
#         "air_transport_lines": [
#             {
#                 "airline_code": "EK",
#                 "loading_port": "DXB",
#                 "first_arrival_port": "MEL"
#                 # Missing weight, date, etc.
#             }
#         ]
#     }

#     result = map_b650_to_formdata(b650_sample)
#     pprint(result)
