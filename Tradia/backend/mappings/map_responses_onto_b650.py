from schemas.B650.import_section_a import B650SectionAHeader
from schemas.B650.import_section_b import SectionB
from schemas.B650.import_section_c_schema import SECTIONC
def map_b650_to_formdata(sectiona: B650SectionAHeader, sectionb: SectionB, sectionc: SECTIONC, 
                         total_price: str, tariff_classification: str):

    print('json recieved')
    """
    Safely converts a JSON object (B650_RESPONSE_FORMAT) into a flat dictionary (form_data)
    used to fill the B650 PDF form.
    Missing fields are filled with empty strings, and missing keys are logged.
    """

    form_data = {}

    # --- HEADER ---
    form_data.update({
        "Import type": sectiona.import_declaration_type or "",
        "Owner Details Owner Name": sectiona.owner_name or "",
        "Owner ID ABN ABNCAC or CCID": sectiona.owner_id or "",
        "Owner Reference": sectiona.owner_reference or "",
        "Biosecurity Inspection Location": sectiona.aqis_inspection_location or "",
        "Owner email": sectiona.contact_details['email'] or "",
        "Destination Port Code": sectiona.destination_port_code or "",
        "Invoice Term Type": sectiona.invoice_term_type or "",
        "Valuation Date": sectiona.valuation_date or "",
        "Header Valuation Advice No": sectiona.header_valuation_advice_number or "",
        "EFT": "Yes",
        "T3": "T3",
        "Declaration": sectiona.declaration_signature or ""
    })



    # Valuation elements → split into Amount/Currency pairs

    form_data.update({
    'Amount1': total_price,
    'Currency1': sectionc.price_currency,
    'Amount2': '',
    'Currency2': '',
    'Amount3': '',
    'Currency3': '',
    'Amount4': '',
    'Currency4': '',
    'Amount5': '',
    'Currency5': '',
    'Amount6': '',
    'Currency6': '',
    'Amount7': '',
    'Currency7': '',
    'Amount8': '',
    'Currency8': '',
    'Amount9': '',
    'Currency9': '',
    })

    # --- AIR TRANSPORT LINES ---
    # for i, line in enumerate(air_lines, start=1):
    #     context = f"air_transport_lines[{i}]"
    #     form_data.update({
    #         "Airline Code": safe_get(line, "airline_code", context),
    #         f"Loading Port{i}": safe_get(line, "loading_port", context),
    #         f"First Arrival Port{i}": safe_get(line, "first_arrival_port", context),
    #         "Discaharge Port1": safe_get(line, "discharge_port", context),
    #         f"First Arrival Date{i}": safe_get(line, "first_arrival_date", context),
    #         f"Gross Weight{i}": safe_get(line, "gross_weight", context),
    #         f"Gross Weight Unit{i}": safe_get(line, "gross_weight_unit", context),
    #         f"Line No{i}": safe_get(line, "line_number", context),
    #         f"Master Air Waybill NoRow{i}": safe_get(line, "master_air_waybill_no", context),
    #         f"House Air Waybill NoRow{i}": safe_get(line, "house_air_waybill_no", context),
    #         f"No of Packages{i}": safe_get(line, "number_of_packages", context),
    #         f"Marks  Numbers DescriptionRow{i}": safe_get(line, "marks_numbers_description", context)
    #     })

    # # --- SEA TRANSPORT LINES ---
    # for idx, line in enumerate(sea_lines, start=1):
    #     suffix = ["", "_2", "_3", "_4"][idx - 1] if idx <= 4 else f"_{idx}"
    #     context = f"sea_transport_lines[{idx}]"
    form_data.update({
        "Vessel Name": sectionb.vessel_name or "",
        "Vessel ID": sectionb.vessel_id or "",
        "Voyage No": sectionb.voyage_number or "",
        "Loading Port_2": sectionb.loading_port or "",
        "First arrival1": sectionb.first_arrival_port or "",
        "Discharge Port_2": sectionb.discharge_port or "",
        "First Arrival Date_2": sectionb.first_arrival_date or "",
        "Gross Weight_2": sectionb.gross_weight or "",
        "Gross Weight Unit_2": sectionb.gross_weight_unit or "",
        "Line No3": sectionb.line_number or "",
        "Cargo TypeRow1": sectionb.cargo_type or "",
        "Container NoRow1": sectionb.container_number or "",
        "Ocean Bill of Lading No1": sectionb.ocean_bill_of_lading_no or "",
        "House Bill of Lading No1": sectionb.house_bill_of_lading_no or "",
        "No of Packages3": sectionb.number_of_packages or "",
        "Marks  Numbers DescriptionRow3": sectionb.marks_numbers_description or ""
    })

    # # --- TARIFF LINES ---

    form_data.update({
        "Tariff Classification No": tariff_classification.replace(".","")  or "",
        "Goods DescriptionC": sectionc.goods_description or "",
        "Quantity1": sectionc.quantity or "",
        "Unit1": sectionc.unit_of_measure,
        "Origin Country1": sectionc.country_of_origin or "",
        "AmountC1": sectionc.customs_value or "",
        "PriceRow1": sectionc.fob_value or "",
        "PriceRow2": sectionc.cif_value or "",
        "Preference Origin Country1": sectionc.origin_country_code or "",
        "Preference Rule Type1": sectionc.preference_rule_type or "",
        "Preference Scheme Type1": sectionc.preference_scheme_type or "",
        "Instrument Type1": sectionc.tariff_instrument or "",
        "Additional Information": sectionc.additional_information or "",
        # "Stat code1": tariff_classification.replace(".","") or ""
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
