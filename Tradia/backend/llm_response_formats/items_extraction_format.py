RESPONSE_FORMAT = {
  "type": "object",
  "properties": {
    "exporter_name": {
      "type": "string",
      "description": "Company name exporting goods"
    },
    "importer_name": {
      "type": "string", 
      "description": "Company name importing goods"
    },
    "port_of_loading": {
      "type": "string",
      "description": "Port where goods are loaded"
    },
    "port_of_discharge": {
      "type": "string",
      "description": "Port where goods are discharged"
    },
    "total_weight": {
      "type": "number",
      "multipleOf": 0.001,
      "description": "Total weight up to 3 decimal places"
    },
    "total_price": {
      "type": "number",
      "multipleOf": 0.01,
      "description": "Total price up to 2 decimal places"
    },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "item_title": {
            "type": "string",
            "maxLength": 255
          },
          "item_weight": {
            "type": "number",
            "multipleOf": 0.001,
            "description": "Item weight up to 3 decimal places"
          },
          "item_weight_unit": {
            "type": "string",
            "maxLength": 10,
            "description": "Weight unit (e.g. 'kg')"
          },
          "item_price": {
            "type": "number",
            "multipleOf": 0.01,
            "description": "Item price up to 2 decimal places"
          },
          "item_currency": {
            "type": "string",
            "pattern": "^[A-Z]{3}$",
            "description": "3-letter ISO currency code (e.g. 'AUD', 'USD')"
          }
        },
        "required": ["item_title"],
        "additionalProperties": False
      }
    }
  },
  "required": [
    "exporter_name",
    "importer_name", 
    "port_of_loading",
    "port_of_discharge",
    "total_weight",
    "total_price",
    "items"
  ],
  "additionalProperties": False
}