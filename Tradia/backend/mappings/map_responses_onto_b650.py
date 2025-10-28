def map_b650_to_formdata(b650_json):
    """
    Converts a JSON object in B650_RESPONSE_FORMAT into a flat dictionary
    that matches the B650 PDF form field schema (form_data).
    """

    form_data = {}

    header = b650_json.get("header", {})
    air_lines = b650_json.get("air_transport_lines", [])
    sea_lines = b650_json.get("sea_transport_lines", [])
    tariff_lines = b650_json.get("tariff_lines", [])

    # --- HEADER ---
    form_data.update({
        "Import type": header.get("import_declaration_type", ""),
        "Owner Details Owner Name": header.get("owner_name", ""),
        "Owner ID ABN ABNCAC or CCID": header.get("owner_id", ""),
        "Owner Reference": header.get("owner_reference", ""),
        "Biosecurity Inspection Location": header.get("aqis_inspection_location", ""),
        "Owner email": header.get("contact_details", ""),
        "Destination Port Code": header.get("destination_port_code", ""),
        "Invoice Term Type": header.get("invoice_term_type", ""),
        "Valuation Date": header.get("valuation_date", ""),
        "Header Valuation Advice No": header.get("header_valuation_advice_number", ""),
        "EFT": header.get("paid_under_protest", ""),
        "T3": header.get("amber_statement_reason", ""),
        "Declaration": header.get("declaration_signature", "")
    })

    # Valuation elements -> split into Amount/Currency pairs
    valuation_elements = header.get("valuation_elements", "")
    if valuation_elements:
        pairs = valuation_elements.split(",")
        for i, pair in enumerate(pairs, 1):
            parts = pair.strip().split()
            if len(parts) == 2:
                form_data[f"Amount{i}"], form_data[f"Currency{i}"] = parts
            elif len(parts) == 1:
                form_data[f"Amount{i}"] = parts[0]

    # --- AIR TRANSPORT LINES ---
    for i, line in enumerate(air_lines, start=1):
        form_data.update({
            f"Airline Code": line.get("airline_code", ""),
            f"Loading Port{i}": line.get("loading_port", ""),
            f"First Arrival Port{i}": line.get("first_arrival_port", ""),
            f"Discaharge Port1": line.get("discharge_port", ""),
            f"First Arrival Date{i}": line.get("first_arrival_date", ""),
            f"Gross Weight{i}": line.get("gross_weight", ""),
            f"Gross Weight Unit{i}": line.get("gross_weight_unit", ""),
            f"Line No{i}": line.get("line_number", ""),
            f"Master Air Waybill NoRow{i}": line.get("master_air_waybill_no", ""),
            f"House Air Waybill NoRow{i}": line.get("house_air_waybill_no", ""),
            f"No of Packages{i}": line.get("number_of_packages", ""),
            f"Marks  Numbers DescriptionRow{i}": line.get("marks_numbers_description", "")
        })

    # --- SEA TRANSPORT LINES ---
    for idx, line in enumerate(sea_lines, start=1):
        suffix = ["", "_2", "_3", "_4"][idx - 1] if idx <= 4 else f"_{idx}"
        form_data.update({
            "Vessel Name": line.get("vessel_name", ""),
            "Vessel ID": line.get("vessel_id", ""),
            "Voyage No": line.get("voyage_number", ""),
            f"Loading Port{suffix}": line.get("loading_port", ""),
            f"First arrival{idx}": line.get("first_arrival_port", ""),
            f"Discharge Port{suffix}": line.get("discharge_port", ""),
            f"First Arrival Date{suffix}": line.get("first_arrival_date", ""),
            f"Gross Weight{suffix}": line.get("gross_weight", ""),
            f"Gross Weight Unit{suffix}": line.get("gross_weight_unit", ""),
            f"Line No{idx+2}": line.get("line_number", ""),
            f"Cargo TypeRow{idx}": line.get("cargo_type", ""),
            f"Container NoRow{idx}": line.get("container_number", ""),
            f"Ocean Bill of Lading No{idx}": line.get("ocean_bill_of_lading_no", ""),
            f"House Bill of Lading No{idx}": line.get("house_bill_of_lading_no", ""),
            f"No of Packages{idx+2}": line.get("number_of_packages", ""),
            f"Marks  Numbers DescriptionRow{idx+2}": line.get("marks_numbers_description", "")
        })

    # --- TARIFF LINES ---
    for i, line in enumerate(tariff_lines, start=1):
        suffix = "" if i == 1 else "_2"
        form_data.update({
            f"Tariff Classification No{suffix}": line.get("tariff_classification", ""),
            f"Goods DescriptionC{suffix}": line.get("goods_description", ""),
            f"Quantity1{suffix}": str(line.get("quantity", "")),
            f"Unit1{suffix}": line.get("unit_of_measure", ""),
            f"Origin Country1{suffix}": line.get("country_of_origin", ""),
            f"AmountC1{suffix}": line.get("customs_value", ""),
            f"PriceRow1{suffix}": line.get("fob_value", ""),
            f"PriceRow2{suffix}": line.get("cif_value", ""),
            f"Preference Origin Country1{suffix}": line.get("origin_country_code", ""),
            f"Preference Rule Type1{suffix}": line.get("preference_rule_type", ""),
            f"Preference Scheme Type1{suffix}": line.get("preference_scheme_type", ""),
            f"Instrument Type1{suffix}": line.get("tariff_instrument", ""),
            f"Additional Information{suffix}": line.get("additional_information", ""),
            f"Stat code1{suffix}": line.get("tariff_classification_code", "")
        })

    return form_data


# Example usage
if __name__ == "__main__":
    from pprint import pprint

    # Sample minimal B650-style JSON
    b650_sample = {
        "header": {
            "import_declaration_type": "s71A",
            "owner_name": "John Doe",
            "owner_id": "123456789",
            "owner_reference": "REF123",
            "aqis_inspection_location": "Sydney Port",
            "contact_details": "john.doe@example.com",
            "destination_port_code": "SYD",
            "invoice_term_type": "FOB",
            "valuation_date": "2025-10-28",
            "header_valuation_advice_number": "VAL001",
            "valuation_elements": "1000 AUD, 200 Freight",
            "fob_or_cif": "FOB",
            "paid_under_protest": "No",
            "amber_statement_reason": "N/A",
            "declaration_signature": "John Doe"
        },
        "air_transport_lines": [
            {
                "airline_code": "QF",
                "loading_port": "SIN",
                "first_arrival_port": "SYD",
                "discharge_port": "SYD",
                "first_arrival_date": "2025-10-25",
                "gross_weight": "1200",
                "gross_weight_unit": "KG",
                "line_number": "1",
                "master_air_waybill_no": "QF123456",
                "house_air_waybill_no": "HAWB001",
                "number_of_packages": "5",
                "marks_numbers_description": "Electronics"
            }
        ],
        "tariff_lines": [
            {
                "tariff_classification": "850440",
                "goods_description": "Power Supply Unit",
                "quantity": 10,
                "unit_of_measure": "EA",
                "country_of_origin": "CN",
                "customs_value": "5000",
                "fob_value": "4800",
                "cif_value": "5200",
                "origin_country_code": "CN",
                "preference_rule_type": "Rule1",
                "preference_scheme_type": "SchemeA",
                "tariff_instrument": "Instrument123",
                "additional_information": "No remarks",
                "tariff_classification_code": "001"
            }
        ]
    }

    # mapped_form_data = map_b650_to_formdata(b650_sample)
    # pprint(mapped_form_data)
