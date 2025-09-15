B650_SECTION_B_SEA_RESPONSE_FORMAT = {
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
        "additionalProperties": False
      }
    },
    
}