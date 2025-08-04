from langchain_openai import ChatOpenAI




llm = ChatOpenAI(
    temperature=0.2,
    model_name=MODEL_NAME,
    openai_api_key=RUNPOD_API_KEY,
    openai_api_base=BASE_URL,       # ← point at RunPod
    # ← you're using an OpenAI-compatible endpoint
)


from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that translates {input_language} to {output_language}.",
        ),
        ("human", "{input}"),
    ]
)

chain = prompt | llm
response = chain.invoke(
    {
        "input_language": "English",
        "output_language": "German",
        "input": "I love programming.",
    }
)

print(response)


# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {RUNPOD_API_KEY}"
# }

# data = {
#     "input": {
#         "prompt": "Hello, how can I assist you today?",
#     }
# }

# try:
#     response = requests.post(BASE_URL, headers=headers, json=data)
#     response.raise_for_status() # Raise an exception for HTTP errors
#     print(response.json())
# except requests.exceptions.RequestException as e:
#     print(f"Error making API call: {e}")
#     if response is not None:
#         print(f"Response content: {response.text}")