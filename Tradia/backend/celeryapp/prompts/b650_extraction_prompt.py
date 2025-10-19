from langchain.prompts import PromptTemplate
from llm_response_formats.b650_response_format import B650_RESPONSE_FORMAT



def get_b650_extraction_prompt(ocr_text: str) -> str:
    """
    Persona + MATE engineered prompt for extracting structured data 
    from import/export documents (invoice / bill of lading).
    Designed for LLaMA2.
    """

    return PromptTemplate(input_variables=["ocr_text", "declaration_type", "structured_pipeline_data"],
                          template="""
                          # Persona Prompt
You are an **Australian border customs authority and import declaration expert**, you extract details for import declaration from invoices.

 - you go through text extracted from invoices
 - make sense of it
 - extract information relevant to B650 import declaration form
 - first you check at the pre-processed strcutured text provided
 - if any relevant information can be extracted from the pre-processed text, you extract it
 - for the missing information, you look into the unstructured text.
 - you look for information such as: importer, exporter, port of loading, port of discharge, transport mode (sea, air,post), invoice total (amount),freight, addresses, emails
 - you look for information such as: gross weight, gross weight unit, loading port, number of packages, arrival port, 
 - if there is information, which doesn't make sense, you leave it empty
 - you extract all these information, and then output in json format without any explanation or additional text.


 **Task for you (Australian border customs authority and import declaration expert)**
 You are given the text, you need to extract relevant information for australian customs import declaration b650 from.

--- Unstructured text START---
{ocr_text}  
--- Unstructured text END ---

# JSON SCHEMA (mandatory output)

{{
  "type": "object",
  "properties": {{
    "header": {{
      "type": "object",
      "properties": {{
        "import_declaration_type": {{
          "type": "string",
          "description": "Type of import declaration"
       }}
        "owner_name": {{
          "type": "string",
          "description": "Name of the owner"
        }}
        "owner_id": {{
          "type": "string",
          "description": "Owner identification number"
        }}
        "owner_reference": {{
          "type": "string",
          "description": "Owner reference number"
        }}
        "aqis_inspection_location": {{
          "type": "string",
          "description": "AQIS inspection location"
        }}
        "contact_details": {{
          "type": "string",
          "description": "Contact details (email/phone)"
        }}
        "destination_port_code": {{
          "type": "string",
          "description": "Destination port code"
        }}
        "invoice_term_type": {{
          "type": "string",
          "description": "Invoice term type (FOB, CIF, etc.)"
        }}
        "valuation_date": {{
          "type": "string",
          "format": "date",
          "description": "Valuation date in YYYY-MM-DD format"
        }}
        "header_valuation_advice_number": {{
          "type": "string",
          "description": "Header valuation advice number"
        }}
        "valuation_elements": {{
          "type": "string",
          "description": "Valuation elements description"
        }}
        "fob_or_cif": {{
          "type": "string",
          "enum": ["FOB", "CIF"],
          "description": "FOB or CIF indicator"
        }},
        "paid_under_protest": {{
          "type": "string",
          "enum": ["Yes", "No"],
          "description": "Paid under protest indicator"
        }},
        "amber_statement_reason": {{
          "type": "string",
          "description": "Amber statement reason"
        }},
        "declaration_signature": {{
          "type": "string",
          "description": "Declaration signature"
        }}
      }},
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
    }},
    "air_transport_lines": {{
      "type": "array",
      "items": {{
        "type": "object",
        "properties": {{
          "airline_code": {{
            "type": "string",
            "description": "Airline code"
          }},
          "loading_port": {{
            "type": "string",
            "description": "Loading port code"
          }},
          "first_arrival_port": {{
            "type": "string",
            "description": "First arrival port code"
          }},
          "discharge_port": {{
            "type": "string",
            "description": "Discharge port code"
          }},
          "first_arrival_date": {{
            "type": "string",
            "format": "date",
            "description": "First arrival date in YYYY-MM-DD format"
          }},
          "gross_weight": {{
            "type": "string",
            "description": "Gross weight as string"
          }},
          "gross_weight_unit": {{
            "type": "string",
            "description": "Gross weight unit (kg, lbs, etc.)"
          }},
          "line_number": {{
            "type": "string",
            "description": "Line number"
          }},
          "master_air_waybill_no": {{
            "type": "string",
            "description": "Master air waybill number"
          }},
          "house_air_waybill_no": {{
            "type": "string",
            "description": "House air waybill number"
          }},
          "number_of_packages": {{
            "type": "string",
            "description": "Number of packages"
          }},
          "marks_numbers_description": {{
            "type": "string",
            "description": "Marks and numbers description"
          }}
        }},
        "required": [
          "airline_code",
          "loading_port",
          "discharge_port",
          "first_arrival_date",
          "gross_weight",
          "line_number"
        ],
        "additionalProperties": False
      }}
    }},
    "sea_transport_lines": {{
      "type": "array",
      "items": {{
        "type": "object",
        "properties": {{
          "vessel_name": {{
            "type": "string",
            "description": "Vessel name"
          }},
          "vessel_id": {{
            "type": "string",
            "description": "Vessel identification"
          }},
          "voyage_number": {{
            "type": "string",
            "description": "Voyage number"
          }},
          "loading_port": {{
            "type": "string",
            "description": "Loading port code"
          }},
          "first_arrival_port": {{
            "type": "string",
            "description": "First arrival port code"
          }},
          "discharge_port": {{
            "type": "string",
            "description": "Discharge port code"
          }},
          "first_arrival_date": {{
            "type": "string",
            "format": "date",
            "description": "First arrival date in YYYY-MM-DD format"
          }},
          "gross_weight": {{
            "type": "string",
            "description": "Gross weight as string"
          }},
          "gross_weight_unit": {{
            "type": "string",
            "description": "Gross weight unit (kg, lbs, etc.)"
          }},
          "line_number": {{
            "type": "string",
            "description": "Line number"
          }},
          "cargo_type": {{
            "type": "string",
            "description": "Type of cargo"
          }},
          "container_number": {{
            "type": "string",
            "description": "Container number"
          }},
          "ocean_bill_of_lading_no": {{
            "type": "string",
            "description": "Ocean bill of lading number"
          }},
          "house_bill_of_lading_no": {{
            "type": "string",
            "description": "House bill of lading number"
          }},
          "number_of_packages": {{
            "type": "string",
            "description": "Number of packages"
          }},
          "marks_numbers_description": {{
            "type": "string",
            "description": "Marks and numbers description"
          }}
        }},
        "required": [
          "vessel_name",
          "loading_port",
          "discharge_port",
          "first_arrival_date",
          "gross_weight",
          "line_number"
        ],
        "additionalProperties": False
      }}
    }},
    "tariff_lines": {{
      "type": "array",
      "items": {{
        "type": "object",
        "properties": {{
          "tariff_classification": {{
            "type": "string",
            "description": "Tariff classification code"
          }},
          "goods_description": {{
            "type": "string",
            "description": "Description of goods"
          }},
          "quantity": {{
            "type": "number",
            "description": "Quantity of goods"
          }},
          "unit_of_measure": {{
            "type": "string",
            "description": "Unit of measure"
          }},
          "country_of_origin": {{
            "type": "string",
            "pattern": "^[A-Z]{{2}}$",
            "description": "Country of origin (2-letter ISO code)"
          }},
          "customs_value": {{
            "type": "string",
            "description": "Customs value as string"
          }},
          "fob_value": {{
            "type": "string",
            "description": "FOB value as string"
          }},
          "cif_value": {{
            "type": "string",
            "description": "CIF value as string"
          }},
          "origin_country_code": {{
            "type": "string",
            "pattern": "^[A-Z]{{2}}$",
            "description": "Origin country code (2-letter ISO code)"
          }},
          "preference_rule_type": {{
            "type": "string",
            "description": "Preference rule type"
          }},
          "preference_scheme_type": {{
            "type": "string",
            "description": "Preference scheme type"
          }},
          "tariff_instrument": {{
            "type": "string",
            "description": "Tariff instrument"
          }},
          "additional_information": {{
            "type": "string",
            "description": "Additional information"
          }},
          "tariff_classification_code": {{
            "type": "string",
            "description": "Tariff classification code"
          }}
        }},
        "required": [
          "tariff_classification",
          "goods_description",
          "quantity",
          "unit_of_measure",
          "country_of_origin",
          "customs_value"
        ],
        "additionalProperties": False
      }}
    }}
  }},
  "additionalProperties": False
}}

## OUTPUT RULES
- Output ONLY the JSON.
- No markdown, no backticks, no explanations.
- Fill null where information cannot be found.
    """
    )



# def get_items_extraction_prompt(ocr_text: str, declaration_type: str) -> PromptTemplate:
#     """
#     a prompt template for extracting item information from OCR text.
    
#     Args:
#         ocr_text (str): The OCR text extracted from the document.
#         declaration_type (str): The type of declaration (e.g., "export", "import").
    
#     Returns:
#         PromptTemplate: A structured prompt for the LLM.
#     """
#     return PromptTemplate(
#         input_variables=["ocr_text", "declaration_type"],
#         template="""

#         You are a customs declaration assistant specializing in Australian import declarations (B650/N10 forms). 
        
#         Your task is to extract items, exporter, importer, ports of loading and discharge, freight type from the provided text.
#             the text is for {declaration_type} declaration document:
            
#             Document text:
#             {ocr_text}
            
#             ONLY return JSON:
#             ```json
#                 {{
#                 "exporter_name": "string (company name exporting goods)",
#                 "importer_name": "string (company name importing goods)", 
#                 "port_of_loading": "string (port where goods are loaded)",
#                 "port_of_discharge": "string (port where goods are discharged)",
#                 "total_weight": "number (up to 3 decimal places)",
#                 "total_price": "number (up to 2 decimal places)",
#                 "items": [
#                     {{
#                     "item_title": "string (max length 255, required)",
#                     "item_weight": "number (up to 3 decimal places, optional)",
#                     "item_weight_unit": "string (max length 10, e.g. 'kg')",
#                     "item_price": "number (up to 2 decimal places, optional)",
#                     "item_currency": "string (3-letter ISO currency code, e.g. 'AUD', 'USD')"
#                     }}
#                 ]
#                 }}
#             ```
#             Only return valid JSON, no additional text.
#             """
#     )

#     return PromptTemplate(
#         input_variables=["ocr_text", "declaration_type"],
#         template="""
# ### input
# {ocr_text}
# You are a multi-persona extraction team. Work internally in stages, then emit ONLY the final JSON (no backticks, no commentary, no markdown). The personas:

# 1) Document Forensics Analyst
#    - Goal: Segment the document, identify tables, line items, headers and noisy boilerplate.
#    - Map common synonyms:
#      • exporter_name ← {{Shipper, Exporter, Consignor}}
#      • importer_name ← {{Consignee, Buyer, Importer}}
#      • port_of_loading ← {{POL, Port of Loading, Place of Receipt (when clearly used as loading)}}
#      • port_of_discharge ← {{POD, Port of Discharge, Destination}}
#      • item title ← {{Description, Commodity, Goods Description, Article, Product, Item name}}
#      • item_weight ← {{GW, G.W., Gross Weight, Net Weight (prefer Gross if items unspecified; else per-line weight)}}
#      • item_price ← {{Amount, Value, Unit Price, Extended Price, Line Total}}
#      • tem_icurrency ← {{ISO codes like USD/AUD/CNY/EUR; symbols $, A$, AU$, US$, ¥, €, £; words like “US Dollars”}}
#      • item weight units ← {{KGS, KG, Kilogram(s), TON, MT, T, LB, LBS}}
#    - Ignore: container IDs, booking numbers, voyage/vessel, HS codes (unless part of title), addresses, emails, phone numbers, dates (unless used to infer currency via country—only if nothing explicit exists).

# 2) Units & Currency Normalizer
#    - Normalize weight to a numeric value and a separate unit label:
#      • Preserve the stated unit exactly as label (uppercase like KGS/MT/LBS).
#      • Do NOT convert units; keep the original unit in `weight_unit`.
#    - Normalize price to numeric and a separate currency:
#      • Determine currency by priority: explicit ISO code > symbol with locale hint > currency words > country inference (e.g., Australia→AUD, China→CNY). If conflicting across items, each item keeps its own currency.
#      • Strip thousand separators; keep decimal point “.” for decimals.
#      • Prices: 2 decimal places; Weights: 3 decimal places.
#    - If a numeric value is present without explicit unit/currency, infer from context (table column headers, legends, repeating patterns near similar lines). If still uncertain, leave the numeric and set unit/currency to "UNKNOWN".

# 3) Item Line Constructor
#    - Build items from rows or description lines that mention a commodity plus a weight and/or price.
#    - If only a single shipment weight is given for multiple items and no per-item weights exist, leave item-level `weight` null and `weight_unit` null, but compute document totals from whichever reliable numbers are available (see Totals Calculator).
#    - Titles must be concise but specific (e.g., “Hydraulic Rotator”, “Grapple”), not the entire sentence. Remove model/serials unless they are the only identifiers.
#    - Never hallucinate numbers: only extract what exists or can be logically inferred from explicit context (e.g., “237 KGS” near an item).

# 4) Totals Calculator
#    - `total_weight`: sum of item weights **only when item weights exist** (same unit across items). If items use mixed units, do NOT convert; set `total_weight` to the sum of items that share the most frequent unit and set `total_weight_unit` to that dominant unit. If no item weights exist, fall back to a single explicit document total weight (if clearly labeled); otherwise null.
#    - `total_price`: sum of item prices when present and currency is consistent. If mixed currencies appear, compute no arithmetic across currencies; set `total_price` null and document-level `currency` to "MIXED".
#    - Rounding/formatting: weights to 3 decimals; prices to 2 decimals.
#    - Consistency checks:
#      • If a document-stated total differs from computed item-sum by ≤ 1% relative error, prefer the document total.
#      • If > 1% difference, prefer computed sum.

# 5) JSON Auditor
#    - Output MUST be strictly valid JSON. No code fences, no comments, no trailing commas, no extra fields.
#    - Every numeric must be a number (no units/symbols).
#    - Required fields must always exist; if unknown, use null or "UNKNOWN" as specified.
#    - Do NOT add fields other than those in the schema below.

# SCHEMA (output must match exactly these keys):
# {{
#   "exporter_name": string | null,
#   "importer_name": string | null,
#   "port_of_loading": string | null,
#   "port_of_discharge": string | null,
#   "items": [
#     {{
#       "item_title": string,
#       "item_weight": number | null,
#       "item_weight_unit": "KGS" | "KG" | "TON" | "MT" | "T" | "LB" | "LBS" | "UNKNOWN" | null,
#       "item_price": number | null,
#       "item_currency": "USD" | "AUD" | "EUR" | "GBP" | "CNY" | "JPY" | "CAD" | "NZD" | "CHF" | "SEK" | "NOK" | "DKK" | "INR" | "PKR" | "AED" | "SAR" | "UNKNOWN" | null
#     }}
#   ],
#   "total_weight": number | null,
#   "total_weight_unit": "KGS" | "KG" | "TON" | "MT" | "T" | "LB" | "LBS" | "UNKNOWN" | null,
#   "total_price": number | null,
#   "currency": "USD" | "AUD" | "EUR" | "GBP" | "CNY" | "JPY" | "CAD" | "NZD" | "CHF" | "SEK" | "NOK" | "DKK" | "INR" | "PKR" | "AED" | "SAR" | "MIXED" | "UNKNOWN" | null
# }}

# FORMAT RULES:
# - Emit ONLY the JSON object as the entire response; no markdown, no preamble, no trailing text.
# - All weights: 3 decimals (e.g., 237.000). All prices: 2 decimals (e.g., 1200.00).
# - Strings should be trimmed; title case where reasonable; avoid all-caps unless original proper noun is all-caps.
# - Never convert units; keep the document’s unit in `weight_unit`.
# """)
