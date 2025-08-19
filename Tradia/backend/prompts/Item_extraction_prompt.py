from langchain.prompts import PromptTemplate

def get_items_extraction_prompt(ocr_text: str, declaration_type: str) -> PromptTemplate:
    """
    Create a prompt template for extracting item information from OCR text.
    
    Args:
        ocr_text (str): The OCR text extracted from the document.
        declaration_type (str): The type of declaration (e.g., "export", "import").
    
    Returns:
        PromptTemplate: A structured prompt for the LLM.
    """
    return PromptTemplate(
        input_variables=["ocr_text", "declaration_type"],
        template="""
            Extract the following information from this {declaration_type} document:
            
            Document text:
            {ocr_text}  # Limit text length
            
            Please extract and return as JSON:
            ```json
                {{
                "exporter_name": "string (company name exporting goods)",
                "importer_name": "string (company name importing goods)", 
                "port_of_loading": "string (port where goods are loaded)",
                "port_of_discharge": "string (port where goods are discharged)",
                "total_weight": "number (up to 3 decimal places)",
                "total_price": "number (up to 2 decimal places)",
                "items": [
                    {{
                    "item_title": "string (max length 255, required)",
                    "item_description": "string (text, optional)",
                    "item_type": "string (max length 100, optional)",
                    "item_weight": "number (up to 3 decimal places, optional)",
                    "item_weight_unit": "string (max length 10, e.g. 'kg')",
                    "item_price": "number (up to 2 decimal places, optional)",
                    "item_currency": "string (3-letter ISO currency code, e.g. 'AUD', 'USD')"
                    }}
                ]
                }}
            ```
            Only return valid JSON, no additional text.
            """
    )
