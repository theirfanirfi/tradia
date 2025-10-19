from langchain.prompts import PromptTemplate



def get_items_extraction_prompt(ocr_text: str, declaration_type: str) -> str:
    """
    Persona + MATE engineered prompt for extracting structured data 
    from import/export documents (invoice / bill of lading).
    Designed for LLaMA2.
    """

    return PromptTemplate(input_variables=["ocr_text", "declaration_type"],
                          template="""
You are a multi-persona expert team working together to extract structured data 
from {declaration_type} documents (commercial invoices, bills of lading, packing lists).
The document text is provided below:

--- DOCUMENT TEXT START ---
{ocr_text}
--- DOCUMENT TEXT END ---

## Document Forensics Analyst
   - Identify exporter, importer, ports, items, and totals.
   - Map synonyms (Shipper/Exporter, Consignee/Importer, POL/Port of Loading, POD/Port of Discharge).

## Units & Currency Normalizer**
   - Extract numeric values separately from their units/symbols.
   - Weights: keep numeric in `item_weight` and `item_weight_unit` separately (e.g., 237 + "KGS").
   - Prices: keep numeric in `item_price` and currency in `item_currency` separately.
   - Normalize formats: weights to 3 decimals, prices to 2 decimals.

## Item Constructor
   - Each item must include: `item_title`, `item_type`, `item_weight`, `item_weight_unit`,
     `item_price`, `item_currency`, and `item_description`.
   - Infer logically if not explicitly labeled (e.g., "GRAPPLE 1 1100 1100 USD" → Grapple, 1100.00 USD).

## JSON Auditor
   - Validate schema.
   - Ensure strictly valid JSON only.
   - No explanations, no markdown, no extra text.

# JSON SCHEMA (mandatory output)

{{
  "exporter_name": "string or null",
  "importer_name": "string or null",
  "consignee": "string or null",
  "buyer": "string or null",
  "port_of_loading": "string or null",
  "port_of_discharge": "string or null",
  "total_weight": "number or null",
  "total_weight_unit": "string or null",
  "total_price": "number or null",
  "currency": "string or null",
  "items": [
    {{
      "item_title": "string (required, max 255)",
      "item_description": "string or null",
      "item_type": "string or null",
      "item_weight": "number or null",
      "item_weight_unit": "string or null",
      "item_price": "number or null",
      "item_currency": "string or null"
    }}
  ]
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
