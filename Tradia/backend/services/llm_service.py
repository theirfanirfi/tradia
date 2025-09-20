import re
from typing import Dict, Any, List, Optional
from config.settings import settings
import json
from ATradiaLLM import llm
from prompts.Item_extraction_prompt import get_items_extraction_prompt
from prompts.B650_section_a_extraction_prompt import get_b650_section_a_extraction_prompt
from prompts.B650_section_b_sea_extraction_prompt import get_b650_section_b_sea_extraction_prompt
from llm_response_formats.B650.Section_a_response_format import B650_SECTION_A_RESPONSE_FORMAT
from llm_response_formats.B650.section_b_air_response_format import SECTION_B_AIR_RESPONSE_FORMAT
from llm_response_formats.B650.section_b_sea_response_format import B650_SECTION_B_SEA_RESPONSE_FORMAT


class LLMService:
    def __init__(self):
        pass

    def process_item_extract_document(self, ocr_text: str, process_id: str, declaration_type: str = "import", response_format: Dict[str, Any]=None) -> Dict[str, Any]:
        """Process OCR text to extract structured information"""
        try:
            # Create prompt for the LLM
            prompt_template = get_items_extraction_prompt(ocr_text, declaration_type)
            prompt = prompt_template.format(ocr_text=ocr_text, declaration_type=declaration_type)
            response = llm._call(prompt=prompt, response_format=response_format)
            print(f"llm_service LLM response: {response}")
            parsed = self.items_to_json(response)
            return parsed
        except Exception as e:
            print(f"llm_service LLM processing error: {e}")
            return False
    
    def items_to_json(self, llm_extracted_items: str) -> List[Dict[str, Any]]:
        pattern = re.compile(r'(\{.*\})', re.DOTALL)

        match = pattern.search(llm_extracted_items)
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            return data
        return False
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured data"""
        try:
            # Try to extract JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1]
            
            data = json.loads(content.strip())
            return data
            
        except (json.JSONDecodeError, IndexError) as e:
            print(f"Failed to parse LLM response: {e}")
            return {}
    
    def process_b650_section_a(self, ocr_text: str, declaration_type: str = "import", structured_data=None) -> Dict[str, Any]:
        """Process OCR text to extract structured information"""
        try:
            # Create prompt for the LLM
            prompt_template = get_b650_section_a_extraction_prompt(ocr_text=ocr_text)
            prompt = prompt_template.format(ocr_text=ocr_text, declaration_type=declaration_type, structured_pipeline_data=structured_data)
            response = llm._call(prompt=prompt, response_format=B650_SECTION_A_RESPONSE_FORMAT)
            print(f"llm_service LLM response: {response}")
            parsed = json.loads(response)
            print(parsed)
            return parsed
        except Exception as e:
            print(f"llm_service LLM processing error: {e}")
            return False
    
    def process_b650_section_b(self, ocr_text: str, declaration_type: str = "import", structured_data=None, mode_of_transport="SEA") -> Dict[str, Any]:
        """Process OCR text to extract structured information FOR SECTION B"""
        try:
            response_format =  None
            prompt_template = get_b650_section_b_sea_extraction_prompt(ocr_text=ocr_text)
            
            if mode_of_transport == "SEA":
                response_format = B650_SECTION_B_SEA_RESPONSE_FORMAT
                prompt_template = get_b650_section_b_sea_extraction_prompt(ocr_text=ocr_text)
            elif mode_of_transport == "AIR":
                response_format = SECTION_B_AIR_RESPONSE_FORMAT
            

            print('response_format',response_format)
            # Create prompt for the LLM
            # prompt_template = get_b650_section_a_extraction_prompt(ocr_text=ocr_text)
            prompt = prompt_template.format(ocr_text=ocr_text, declaration_type=declaration_type, structured_pipeline_data=structured_data)
            response = llm._call(prompt=prompt, response_format=response_format)
            print(f"llm_service LLM response: {response}")
            parsed = json.loads(response)
            print(parsed)
            return parsed
        except Exception as e:
            print(f"llm_service LLM processing error: {e}")
            return False

# Global instance
llm_service = LLMService()
