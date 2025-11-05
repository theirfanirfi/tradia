# from langchain_core.prompts import PromptTemplate

# def get_b650_section_a_extraction_prompt(ocr_text: str) -> str:
#     """
#     Returns a structured prompt for extracting B650 (N10) Import Declaration data
#     from OCR-extracted invoice text. This integrates layout- and multi-page-aware
#     extraction logic aligned with Australian customs requirements.
#     """
#     return PromptTemplate(
#         input_variables=["ocr_text", "declaration_type", "structured_pipeline_data"],
#         template="""
# # ROLE & PURPOSE
# You are an **expert customs import declaration officer** for the Australian Border Force,
# skilled at interpreting trade invoices, bills of lading, and packing lists for the
# **Import Declaration (N10) – B650 form (approved under Section 71K of the Customs Act 1901)**.

# Your job:
# - Read through both structured and unstructured OCR text.
# - Extract all relevant information required for completing the Australian Import Declaration (N10).
# - Handle **multi-page invoices**, **scanned text**, and **semi-structured data** robustly.
# - Follow official mapping of Sections A, B, and C as per form B650 (Design 03/19a).
# - Output valid JSON conforming to the schema below — **no explanations or additional text**.

# ---

# ## EXTRACTION STRATEGY

# 1. **Pre-processing logic:**
#    - Start by checking structured pre-processed data in `{structured_pipeline_data}`.
#    - Use this to fill fields wherever data is clearly available.
#    - For missing fields, fall back to parsing `{ocr_text}` (unstructured text).

# 2. **Contextual understanding:**
#    - Make sense of layout: key-value pairs, tables, line items, shipping terms, etc.
#    - Normalize multi-page content into a single JSON output.
#    - Ignore OCR artifacts, disclaimers, and irrelevant text.

# 3. **Field extraction order:**
#    - Owner details: owner name, owner id (ABN, CAC, or CCID), owner reference, AQIS inspection location.
#    - Contact details: email, phone, mobile.
#    - Shipment and financials: destination port code, invoice term type (FOB/CIF), valuation date, valuation advice number.
#    - Values and indicators: valuation elements, FOB/CIF indicator, paid under protest, amber statement reason.
#    - Declaration signature: name or entity signing the declaration.

# 4. **Table awareness:**
#    - Detect product or goods tables — columns like “Description”, “Quantity”, “Unit”, “Origin Country”, “Value”.
#    - Each row → one `tariff_line` entry.
#    - Merge continued rows across multiple pages.

# 5. **Normalization rules:**
#    - Dates → YYYY-MM-DD
#    - Currency → retain ISO code (AUD, USD, etc.)
#    - Quantity → numeric only
#    - Units → plain text (e.g., KG, PCS)
#    - Missing values → null or empty string

# 6. **Output rule:**
#    - **Only output the JSON**, nothing else.
#    - Ensure JSON is syntactically valid and adheres to schema.
#    - No markdown or formatting.

# ---

# ## JSON SCHEMA (MANDATORY OUTPUT)
# {{
#   "type": "object",
#   "properties": {{
#     "header": {{
#       "type": "object",
#       "properties": {{
#         "import_declaration_type": {{
#           "type": "string",
#           "description": "Type of import declaration (e.g., s71A)"
#         }},
#         "owner_name": {{
#           "type": "string",
#           "description": "Name of the owner"
#         }},
#         "owner_id": {{
#           "type": "string",
#           "description": "Owner identification number"
#         }},
#         "owner_reference": {{
#           "type": "string",
#           "description": "Owner reference number"
#         }},
#         "aqis_inspection_location": {{
#           "type": "string",
#           "description": "AQIS inspection location"
#         }},
#         "contact_details": {{
#           "type": "object",
#           "properties": {{
#             "mobile": {{"type": "string"}},
#             "email": {{"type": "string"}},
#             "phone": {{"type": "string"}}
#           }},
#           "description": "Contact details (email, phone, or mobile)"
#         }},
#         "destination_port_code": {{
#           "type": "string",
#           "description": "Destination port code"
#         }},
#         "invoice_term_type": {{
#           "type": "string",
#           "description": "Invoice term type (FOB, CIF, etc.)"
#         }},
#         "valuation_date": {{
#           "type": "string",
#           "format": "date",
#           "description": "Valuation date in YYYY-MM-DD format"
#         }},
#         "header_valuation_advice_number": {{
#           "type": "string",
#           "description": "Header valuation advice number"
#         }},
#         "valuation_elements": {{
#           "type": "object",
#           "description": "Valuation elements (invoice total, freight, insurance, packing, etc.)"
#         }},
#         "fob_or_cif": {{
#           "type": "string",
#           "enum": ["FOB", "CIF"],
#           "description": "FOB or CIF indicator"
#         }},
#         "paid_under_protest": {{
#           "type": "string",
#           "enum": ["Yes", "No"],
#           "description": "Paid under protest indicator"
#         }},
#         "amber_statement_reason": {{
#           "type": "string",
#           "description": "Amber statement reason"
#         }},
#         "declaration_signature": {{
#           "type": "string",
#           "description": "Declaration signature"
#         }}
#       }},
#       "additionalProperties": false
#     }},
#     "tariff_lines": {{
#       "type": "array",
#       "description": "Tariff classification details for goods",
#       "items": {{
#         "type": "object",
#         "properties": {{
#           "tariff_classification": {{"type": "string"}},
#           "goods_description": {{"type": "string"}},
#           "quantity": {{"type": "number"}},
#           "unit_of_measure": {{"type": "string"}},
#           "country_of_origin": {{"type": "string"}},
#           "customs_value": {{"type": "string"}},
#           "fob_value": {{"type": "string"}},
#           "cif_value": {{"type": "string"}},
#           "origin_country_code": {{"type": "string"}},
#           "preference_rule_type": {{"type": "string"}},
#           "preference_scheme_type": {{"type": "string"}},
#           "tariff_instrument": {{"type": "string"}},
#           "additional_information": {{"type": "string"}},
#           "tariff_classification_code": {{"type": "string"}}
#         }},
#         "additionalProperties": false
#       }}
#     }}
#   }},
#   "required": ["header", "tariff_lines"],
#   "additionalProperties": false
# }}

# ---

# ## INPUTS

# Structured pre-processed data:
# {structured_pipeline_data}

# Unstructured OCR text:
# {ocr_text}

# ---

# ## OUTPUT RULES
# - Output strictly valid JSON.
# - No markdown, no commentary.
# - Use null or empty string for missing values.
#         """
#     )



from langchain_core.prompts import PromptTemplate
def get_b650_section_a_extraction_prompt(ocr_text: str) -> str:
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
 - At first you look for these information: owner name, owner id, owner reference, inspection location, owner contact details,
 - then you look for these information: destination port cdoe, invoice term type, valuation date, valuation advice number, FOB or CIF indicator,
 - at last you look for these information: paid under protest, statement reason, and declaration signature
 - if there is information, which doesn't make sense, you leave it empty
 - you extract all these information, and then output in json format without any explanation or additional text.


 **Task for you (Australian border customs authority and import declaration expert)**
 You are given the text, you need to extract relevant information for australian customs import declaration b650 from.

--- Here is the structured and unstructured data combined ---
{structured_pipeline_data}

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
          "description": "Type of import declaration (e.g., s71A)"
        }},
        "owner_name": {{
          "type": "string",
          "description": "Name of the owner"
        }},
        "owner_id": {{
          "type": "string",
          "description": "Owner identification number"
        }},
        "owner_reference": {{
          "type": "string",
          "description": "Owner reference number"
        }},
        "aqis_inspection_location": {{
          "type": "string",
          "description": "AQIS inspection location"
        }},
        "contact_details": {{
          "type": "object",
          "properties": {{
          "mobile":{{
          "type": "string",
          }}

          "email":{{
          "type": "string",
          }}

        "phone":{{
          "type": "string",
          }}
          }}
          "description": "Contact details (email or phone)"
        }},
        "destination_port_code": {{
          "type": "string",
          "description": "Destination port code"
        }},
        "invoice_term_type": {{
          "type": "string",
          "description": "Invoice term type (FOB, CIF, etc.)"
        }},
        "valuation_date": {{
          "type": "string",
          "format": "date",
          "description": "Valuation date in YYYY-MM-DD format"
        }},
        "header_valuation_advice_number": {{
          "type": "string",
          "description": "Header valuation advice number"
        }},
        "valuation_elements": {{
          "type": "object",
          "description": "Valuation elements description"
        }},
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
      "additionalProperties": false
    }},
    "tariff_lines": {{
      "type": "array",
      "description": "Tariff classification details for goods",
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
            "description": "Country of origin"
          }},
          "customs_value": {{
            "type": "string",
            "description": "Declared customs value"
          }},
          "fob_value": {{
            "type": "string",
            "description": "FOB (Free on Board) value"
          }},
          "cif_value": {{
            "type": "string",
            "description": "CIF (Cost, Insurance, and Freight) value"
          }},
          "origin_country_code": {{
            "type": "string",
            "description": "Country code of origin"
          }},
          "preference_rule_type": {{
            "type": "string",
            "description": "Type of preference rule"
          }},
          "preference_scheme_type": {{
            "type": "string",
            "description": "Preference scheme type"
          }},
          "tariff_instrument": {{
            "type": "string",
            "description": "Applicable tariff instrument"
          }},
          "additional_information": {{
            "type": "string",
            "description": "Additional relevant information"
          }},
          "tariff_classification_code": {{
            "type": "string",
            "description": "Tariff classification reference code"
          }}
        }},
        "additionalProperties": false
      }}
    }}
  }},
  "required": ["header","tariff_lines"],
  "additionalProperties": false
}}


## OUTPUT RULES
- Output ONLY the JSON.
- No markdown, no backticks, no explanations.
- Fill null where information cannot be found.
    """
)

