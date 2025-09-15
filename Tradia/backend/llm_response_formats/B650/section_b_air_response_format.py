SECTION_B_AIR_RESPONSE_FORMAT= {    
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
    "additionalProperties": False
    }
},
}

    