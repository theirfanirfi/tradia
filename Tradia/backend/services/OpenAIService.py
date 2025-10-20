import json
import re
import logging
from typing import Dict, Any, List, Optional

from config.settings import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Example imports – adjust paths to your project structure
from prompts.Item_extraction_prompt import get_items_extraction_prompt
from prompts.B650_section_a_extraction_prompt import get_b650_section_a_extraction_prompt
from prompts.B650_section_b_sea_extraction_prompt import get_b650_section_b_sea_extraction_prompt
from prompts.B650_section_c_extraction_prompt import get_b650_section_c_extraction_prompt

from llm_response_formats.B650.Section_a_response_format import B650_SECTION_A_RESPONSE_FORMAT
from llm_response_formats.B650.section_b_air_response_format import SECTION_B_AIR_RESPONSE_FORMAT
from llm_response_formats.B650.section_b_sea_response_format import B650_SECTION_B_SEA_RESPONSE_FORMAT
from llm_response_formats.B650.section_c_response_format import SECTION_C


class OpenAIService:
    """
    Service layer for OpenAI LLM via LangChain.
    Provides structured information extraction for OCR text.
    """

    def __init__(self):
        logging.info(settings.OPENAI_API_KEY)
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.2,
        )
        self.parser = StrOutputParser()

    # --------------------------
    # GENERIC LLM CALL HANDLER
    # --------------------------
    def _call_llm(
        self,
        prompt: str,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Internal helper to invoke OpenAI LLM and return raw text.
        """
        try:
            logging.info("Sending prompt to OpenAI model.")
            response = self.llm.invoke(prompt)
            logging.info(f"response openai {response}")
            text = response.content if hasattr(response, "content") else str(response)
            return text
        except Exception as e:
            logging.exception(f"OpenAI LLM call failed: {e}")
            raise RuntimeError(f"LLM call failed: {str(e)}")

    # --------------------------
    # ITEM EXTRACTION
    # --------------------------
    def process_item_extract_document(
        self,
        ocr_text: str,
        process_id: str,
        declaration_type: str = "import",
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process OCR text to extract structured item information.
        """
        try:
            prompt_template = get_items_extraction_prompt(ocr_text, declaration_type)
            prompt = prompt_template.format(
                ocr_text=ocr_text, declaration_type=declaration_type
            )

            response = self._call_llm(prompt, response_format)
            parsed = self._parse_to_json(response)
            return parsed
        except Exception as e:
            logging.error(f"process_item_extract_document error: {e}")
            return {"success": False, "error": str(e)}

    # --------------------------
    # SECTION A
    # --------------------------
    def process_b650_section_a(
        self,
        ocr_text: str,
        declaration_type: str = "import",
        structured_data=None,
    ) -> Dict[str, Any]:
        """
        Extract structured information for Section A.
        """
        try:
            prompt_template = get_b650_section_a_extraction_prompt(ocr_text=ocr_text)
            prompt = prompt_template.format(
                ocr_text=ocr_text,
                declaration_type=declaration_type,
                structured_pipeline_data=structured_data,
            )

            response = self._call_llm(prompt, B650_SECTION_A_RESPONSE_FORMAT)
            parsed = self._parse_to_json(response)
            return parsed
        except Exception as e:
            logging.error(f"process_b650_section_a error: {e}")
            return {"success": False, "error": str(e)}

    # --------------------------
    # SECTION B
    # --------------------------
    def process_b650_section_b(
        self,
        ocr_text: str,
        declaration_type: str = "import",
        structured_data=None,
        mode_of_transport: str = "SEA",
    ) -> Dict[str, Any]:
        """
        Extract structured information for Section B.
        Supports SEA and AIR.
        """
        try:
            if mode_of_transport.upper() == "SEA":
                response_format = B650_SECTION_B_SEA_RESPONSE_FORMAT
                prompt_template = get_b650_section_b_sea_extraction_prompt(
                    ocr_text=ocr_text
                )
            else:
                response_format = SECTION_B_AIR_RESPONSE_FORMAT
                prompt_template = get_b650_section_b_sea_extraction_prompt(
                    ocr_text=ocr_text
                )

            prompt = prompt_template.format(
                ocr_text=ocr_text,
                declaration_type=declaration_type,
                structured_pipeline_data=structured_data,
            )

            response = self._call_llm(prompt, response_format)
            parsed = self._parse_to_json(response)
            return parsed
        except Exception as e:
            logging.error(f"process_b650_section_b error: {e}")
            return {"success": False, "error": str(e)}

    # --------------------------
    # SECTION C
    # --------------------------
    def process_b650_section_c(
        self,
        ocr_text: str,
        declaration_type: str = "import",
        structured_data=None,
    ) -> Dict[str, Any]:
        """
        Extract structured information for Section C.
        """
        try:
            prompt_template = get_b650_section_c_extraction_prompt(ocr_text=ocr_text)
            prompt = prompt_template.format(
                ocr_text=ocr_text,
                declaration_type=declaration_type,
                structured_pipeline_data=structured_data,
            )

            response = self._call_llm(prompt, SECTION_C)
            parsed = self._parse_to_json(response)
            return parsed
        except Exception as e:
            logging.error(f"process_b650_section_c error: {e}")
            return {"success": False, "error": str(e)}

    # --------------------------
    # UTILITY PARSERS
    # --------------------------
    def _parse_to_json(self, response_text: str) -> Any:
        """
        Attempt to extract JSON object from LLM text output.
        """
        try:
            # Try to find JSON block in markdown style responses
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1]

            # Fallback: match {...}
            match = re.search(r"(\{.*\})", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)

            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            logging.warning("Failed to parse JSON. Returning raw text.")
            return {"raw_response": response_text}


# Global instance for reuse
openai_llm_service = OpenAIService()
