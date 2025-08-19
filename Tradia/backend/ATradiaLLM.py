import asyncio
import httpx
from typing import Optional, List
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OLLAMA_MODEL = "llama2"


class AsyncTradiaLLM(LLM):
    """Async Custom LLM class for interacting with EC2-hosted LLM API."""

    ec2_url: str  # Base URL e.g., "http://ec2-ip:11434/api/generate"

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        """Async call to the LLM API."""
        try:
            payload = {"prompt": prompt, "stream": False, "model": OLLAMA_MODEL}
            headers = {"Content-Type": "application/json"}

            # Use httpx for async HTTP requests with proper timeout
            timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Sending request to LLM: {self.ec2_url}")
                response = await client.post(self.ec2_url, json=payload, headers=headers)
                response.raise_for_status()
                json_data = response.json()

                if "error" in json_data:
                    raise ValueError(f"EC2 LLM Error: {json_data['error']}")

                result = json_data.get("response", "")
                print(result)
                logger.info(f"Received LLM response (length: {len(result)})")
                return result

        except httpx.TimeoutException as e:
            logger.error(f"LLM request timed out: {str(e)}")
            raise ValueError(f"LLM request timed out after 5 minutes: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"HTTP error from LLM: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {str(e)}")
            raise ValueError(f"Request failed: {str(e)}")

    async def _astream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ):
        """Async streaming call to the LLM API."""
        try:
            payload = {"prompt": prompt, "stream": True, "model": OLLAMA_MODEL}
            headers = {"Content-Type": "application/json"}

            # Use httpx for async HTTP requests with proper timeout
            timeout = httpx.Timeout(connect=30.0, read=800.0, write=30.0, pool=30.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(f"Sending streaming request to LLM: {self.ec2_url}")
                async with client.stream("POST", self.ec2_url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                json_data = json.loads(line)
                                
                                if "error" in json_data:
                                    raise ValueError(f"EC2 LLM Error: {json_data['error']}")
                                
                                if "response" in json_data:
                                    print(f"Streaming response: {json_data['response']}")
                                    yield json_data["response"]
                                
                                if json_data.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError:
                                continue

        except httpx.TimeoutException as e:
            logger.error(f"LLM streaming request timed out: {str(e)}")
            raise ValueError(f"LLM streaming request timed out: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"HTTP error from LLM: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error in streaming LLM: {str(e)}")
            raise ValueError(f"Streaming request failed: {str(e)}")

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
            """Synchronous call to the LLM API."""
            print(f"Calling LLM with prompt: ...")  # Log first 100 chars of prompt
            try:
                payload = {"prompt": prompt, "stream": False, "model": OLLAMA_MODEL}
                headers = {"Content-Type": "application/json"}

                timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)

                print(f"Sending SYNC request to LLM: {self.ec2_url}")
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(self.ec2_url, json=payload, headers=headers)
                    response.raise_for_status()
                    json_data = response.json()
                    print(json_data)

                if "error" in json_data:
                    raise ValueError(f"EC2 LLM Error: {json_data['error']}")

                result = json_data.get("response", "")
                
                print(f"Received LLM response (length: {len(result)})")
                return result

            except httpx.TimeoutException as e:
                print(f"LLM request timed out: {str(e)}")
                raise ValueError(f"LLM request timed out after 5 minutes: {str(e)}")
            except httpx.HTTPStatusError as e:
                print(f"HTTP error from LLM: {e.response.status_code} - {e.response.text}")
                raise ValueError(f"HTTP error from LLM: {e.response.status_code}")
            except Exception as e:
                print(f"Unexpected error calling LLM: {str(e)}")
                raise ValueError(f"Request failed: {str(e)}")

    @property
    def _llm_type(self) -> str:
        return "async-ec2-tradia-llama2"

# Initialize the async LLM
llm = AsyncTradiaLLM(ec2_url="http://localhost:11434/api/generate")
