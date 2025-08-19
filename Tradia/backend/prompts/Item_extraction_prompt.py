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
                "exporter_name": "Company name exporting goods",
                "importer_name": "Company name importing goods", 
                "port_of_loading": "Port where goods are loaded",
                "port_of_discharge": "Port where goods are discharged",
                "total_weight": "Total weight in kg",
                "total_value": "Total value in AUD",
                "items": [
                    {{
                        "item_title": "Item name/description",
                        "item_description": "Detailed description",
                        "item_type": "Type/category of item",
                        "item_weight": "Weight in kg",
                        "item_weight_unit": "kg",
                        "item_price": "Price in AUD",
                        "item_currency": "AUD"
                    }}
                ]
            }}
            ```
            Only return valid JSON, no additional text.
            """
    )
