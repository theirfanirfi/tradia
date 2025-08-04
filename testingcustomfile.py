from typing import Optional, List
import requests
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
OLLAMA_MODEL = "llama2"

class TradiaLLM(LLM):
    """Custom LLM class for interacting with EC2-hosted LLM API."""

    ec2_url: str  # Base URL e.g., "https://ec2-ip:11434/api/ask"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        # Compose URL
        try:
            payload = {"prompt": prompt, "stream": False, "model": OLLAMA_MODEL}
            headers = {"Content-Type": "application/json"}

            response = requests.post(self.ec2_url, json=payload, headers=headers, timeout=1000)
            response.raise_for_status()
            json_data = response.json()

            if "error" in json_data:
                raise ValueError(f"EC2 LLM Error: {json_data['error']}")

            return json_data.get("response", "")

        except Exception as e:
            raise ValueError(f"Request failed: {str(e)}")

    @property
    def _llm_type(self) -> str:
        return "ec2-tradia-llama2"




# from langchain_core.prompts import ChatPromptTemplate

# Instantiate custom LLM
tradiaLLM = TradiaLLM(ec2_url="http://3.27.244.65:11434/api/generate")

# # Prompt template
# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are a helpful assistant that translates {input_language} to {output_language}.",
#         ),
#         ("human", "{input}"),
#     ]
# )

# chain = prompt | tradiaLLM
# response = chain.invoke(
#     {
#         "input_language": "English",
#         "output_language": "German",
#         "input": "I love programming.",
#     }
# )

# print(response)
