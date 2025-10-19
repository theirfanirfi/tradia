B650_RESPONSE_FORMAT = {
  "type": "object",
  "properties": {
    "header": {
      "type": "object",
      "properties": {
        "import_declaration_type": {
          "type": "string",
          "description": "Type of import declaration"
        },
        "owner_name": {
          "type": "string",
          "description": "Name of the owner"
        },
        "owner_id": {
          "type": "string",
          "description": "Owner identification number"
        },
        "owner_reference": {
          "type": "string",
          "description": "Owner reference number"
        },
        "aqis_inspection_location": {
          "type": "string",
          "description": "AQIS inspection location"
        },
        "contact_details": {
          "type": "string",
          "description": "Contact details (email/phone)"
        },
        "destination_port_code": {
          "type": "string",
          "description": "Destination port code"
        },
        "invoice_term_type": {
          "type": "string",
          "description": "Invoice term type (FOB, CIF, etc.)"
        },
        "valuation_date": {
          "type": "string",
          "format": "date",
          "description": "Valuation date in YYYY-MM-DD format"
        },
        "header_valuation_advice_number": {
          "type": "string",
          "description": "Header valuation advice number"
        },
        "valuation_elements": {
          "type": "string",
          "description": "Valuation elements description"
        },
        "fob_or_cif": {
          "type": "string",
          "enum": ["FOB", "CIF"],
          "description": "FOB or CIF indicator"
        },
        "paid_under_protest": {
          "type": "string",
          "enum": ["Yes", "No"],
          "description": "Paid under protest indicator"
        },
        "amber_statement_reason": {
          "type": "string",
          "description": "Amber statement reason"
        },
        "declaration_signature": {
          "type": "string",
          "description": "Declaration signature"
        }
      },
      "required": [
        "import_declaration_type",
        "owner_name",
        "owner_id",
        "destination_port_code",
        "invoice_term_type",
        "valuation_date",
        "fob_or_cif",
        "paid_under_protest",
        "declaration_signature"
      ],
      "additionalProperties": False
    },
    "air_transport_lines": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "airline_code": {
            "type": "string",
            "description": "Airline code"
          },
          "loading_port": {
            "type": "string",
            "description": "Loading port code"
          },
          "first_arrival_port": {
            "type": "string",
            "description": "First arrival port code"
          },
          "discharge_port": {
            "type": "string",
            "description": "Discharge port code"
          },
          "first_arrival_date": {
            "type": "string",
            "format": "date",
            "description": "First arrival date in YYYY-MM-DD format"
          },
          "gross_weight": {
            "type": "string",
            "description": "Gross weight as string"
          },
          "gross_weight_unit": {
            "type": "string",
            "description": "Gross weight unit (kg, lbs, etc.)"
          },
          "line_number": {
            "type": "string",
            "description": "Line number"
          },
          "master_air_waybill_no": {
            "type": "string",
            "description": "Master air waybill number"
          },
          "house_air_waybill_no": {
            "type": "string",
            "description": "House air waybill number"
          },
          "number_of_packages": {
            "type": "string",
            "description": "Number of packages"
          },
          "marks_numbers_description": {
            "type": "string",
            "description": "Marks and numbers description"
          }
        },
        "required": [
          "airline_code",
          "loading_port",
          "discharge_port",
          "first_arrival_date",
          "gross_weight",
          "line_number"
        ],
        "additionalProperties": False
      }
    },
    "sea_transport_lines": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "vessel_name": {
            "type": "string",
            "description": "Vessel name"
          },
          "vessel_id": {
            "type": "string",
            "description": "Vessel identification"
          },
          "voyage_number": {
            "type": "string",
            "description": "Voyage number"
          },
          "loading_port": {
            "type": "string",
            "description": "Loading port code"
          },
          "first_arrival_port": {
            "type": "string",
            "description": "First arrival port code"
          },
          "discharge_port": {
            "type": "string",
            "description": "Discharge port code"
          },
          "first_arrival_date": {
            "type": "string",
            "format": "date",
            "description": "First arrival date in YYYY-MM-DD format"
          },
          "gross_weight": {
            "type": "string",
            "description": "Gross weight as string"
          },
          "gross_weight_unit": {
            "type": "string",
            "description": "Gross weight unit (kg, lbs, etc.)"
          },
          "line_number": {
            "type": "string",
            "description": "Line number"
          },
          "cargo_type": {
            "type": "string",
            "description": "Type of cargo"
          },
          "container_number": {
            "type": "string",
            "description": "Container number"
          },
          "ocean_bill_of_lading_no": {
            "type": "string",
            "description": "Ocean bill of lading number"
          },
          "house_bill_of_lading_no": {
            "type": "string",
            "description": "House bill of lading number"
          },
          "number_of_packages": {
            "type": "string",
            "description": "Number of packages"
          },
          "marks_numbers_description": {
            "type": "string",
            "description": "Marks and numbers description"
          }
        },
        "required": [
          "vessel_name",
          "loading_port",
          "discharge_port",
          "first_arrival_date",
          "gross_weight",
          "line_number"
        ],
        "additionalProperties": False
      }
    },
    "tariff_lines": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "tariff_classification": {
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
            "description": "Unit of measure"
          },
          "country_of_origin": {
            "type": "string",
            "pattern": "^[A-Z]{2}$",
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
            "pattern": "^[A-Z]{2}$",
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
          "tariff_classification_code": {
            "type": "string",
            "description": "Tariff classification code"
          }
        },
        "required": [
          "tariff_classification",
          "goods_description",
          "quantity",
          "unit_of_measure",
          "country_of_origin",
          "customs_value"
        ],
        "additionalProperties": False
      }
    }
  },
  "additionalProperties": False
}