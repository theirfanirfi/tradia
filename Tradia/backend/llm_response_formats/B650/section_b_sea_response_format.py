B650_SECTION_B_SEA_RESPONSE_FORMAT = {
  "type": "object",
  "properties": {
    "sea_transport_lines": {
      "type": "object",
      "properties": {
        "mode_of_transport": {
          "type": "string",
          "description": "SEA"
        },
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
        "vessel_id",
        "voyage_number",
        "loading_port",
        "first_arrival_port",
        "discharge_port",
        "first_arrival_date",
        "gross_weight",
        "gross_weight_unit",
        "line_number",
        "cargo_type",
        "container_number",
        "ocean_bill_of_lading_no",
        "number_of_packages"
      ],
      "additionalProperties": False
    }
  }
}
