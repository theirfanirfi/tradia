SECTION_C = {
    "type": "object",
    "properties": {
        "tariff_lines": {
            "type": "object",
            "properties": {
                "tariff_classification_code": {
                    "type": "string",
                    "description": "Tariff classification code"
                },
                "goods_description": {
                    "type": "string",
                    "description": "Description of goods"
                },
                "quantity": {
                    "type": "number",
                    "description": "Quantity of goods"
                },
                "unit_of_measure": {
                    "type": "string",
                    "description": "Unit of measure (e.g., KGS, LBS)"
                },
                "country_of_origin": {
                    "type": "string",
                    "description": "Country of origin (2-letter ISO code)"
                },
                "customs_value": {
                    "type": "string",
                    "description": "Customs value as string"
                },
                "fob_value": {
                    "type": "string",
                    "description": "FOB value as string"
                },
                "cif_value": {
                    "type": "string",
                    "description": "CIF value as string"
                },
                "origin_country_code": {
                    "type": "string",
                    "description": "Origin country code (2-letter ISO code)"
                },
                "preference_rule_type": {
                    "type": "string",
                    "description": "Preference rule type"
                },
                "preference_scheme_type": {
                    "type": "string",
                    "description": "Preference scheme type"
                },
                "tariff_instrument": {
                    "type": "string",
                    "description": "Tariff instrument"
                },
                "additional_information": {
                    "type": "string",
                    "description": "Additional information"
                },
                "supplier_id": {
                    "type": "string",
                    "description": "Supplier ID"
                },
                "supplier_name": {
                    "type": "string",
                    "description": "Supplier name"
                },
                "vendor_id": {
                    "type": "string",
                    "description": "Vendor ID"
                },
                "stat_code": {
                    "type": "string",
                    "description": "Statistical code"
                },
                "valuation_basis_type": {
                    "type": "string",
                    "description": "Valuation basis type"
                },
                "treatment_code": {
                    "type": "string",
                    "description": "Treatment code"
                },
                "gst_exemption_code": {
                    "type": "string",
                    "description": "GST exemption code"
                },
                "establishment_code": {
                    "type": "string",
                    "description": "Establishment code"
                },
                "price_type": {
                    "type": "string",
                    "description": "Price type (CIF, FOB, CUSTOMS)"
                },
                "price_amount": {
                    "type": "string",
                    "description": "Price amount"
                },
                "price_currency": {
                    "type": "string",
                    "description": "Price currency, e.g. AUD"
                },
                "permit_number": {
                    "type": "string",
                    "description": "Permit number"
                },
                "preference_origin_country": {
                    "type": "string",
                    "description": "Preference origin country"
                },
                "instrument_type1": {
                    "type": "string",
                    "description": "Instrument type 1"
                },
                "instrument_number1": {
                    "type": "string",
                    "description": "Instrument number 1"
                },
                "instrument_type2": {
                    "type": "string",
                    "description": "Instrument type 2"
                },
                "instrument_number2": {
                    "type": "string",
                    "description": "Instrument number 2"
                },
                "producer_code": {
                    "type": "string",
                    "description": "Producer code"
                }
            },
            "additionalProperties": False
        }
    }
}
