B650_SECTION_A_RESPONSE_FORMAT = {
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
  }
}