from typing import Optional, List
import httpx
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import (
    CallbackManagerForLLMRun,
    AsyncCallbackManagerForLLMRun
)
from pydantic import BaseModel


class ATradiaLLM(LLM, BaseModel):
    ec2_url: str
    timeout: int = 600  # 10 minutes

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        raise NotImplementedError("This LLM only supports async. Use `await chain.ainvoke(...)`.")

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
    ) -> str:
        payload = {"query": prompt}
        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.ec2_url, json=payload, headers=headers)

                # Ensure the entire response body is read
                raw_text = await response.aread()
                response.raise_for_status()

                # Parse JSON manually from raw bytes
                json_data = httpx.Response._json_decoder(raw_text.decode())

                if "error" in json_data:
                    raise ValueError(f"EC2 LLM Error: {json_data['error']}")
                return json_data.get("response", "")

        except httpx.TimeoutException:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds.")

        except httpx.RequestError as e:
            raise ValueError(f"Request failed: {str(e)}")

        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")

    @property
    def _llm_type(self) -> str:
        return "ec2-custom-llm"



atradiaLLM = ATradiaLLM(ec2_url="http://3.27.244.65:8000/ask", timeout=1000)