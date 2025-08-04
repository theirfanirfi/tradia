import os
from typing import Type
from pathlib import Path

from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser

from forms_schema.b650_schema import B650Model
from forms_schema.b957_schema import B957ExportDeclaration

from langchain_core.prompts import ChatPromptTemplate


# ROOT will be backend/, because this file lives in backend/core
ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "forms_schema"

B650_SAMPLE_PATH = os.path.join(SCHEMA_DIR, 'b650_sample.json')
with open(B650_SAMPLE_PATH, 'r') as f:
    B650_SAMPLE_JSON = f.read().replace("{","{{").replace("}","}}")

B957_SAMPLE_PATH = os.path.join(SCHEMA_DIR, 'b957_sample.json')
with open(B957_SAMPLE_PATH, 'r') as f:
    B957_SAMPLE_JSON = f.read().replace("{","{{").replace("}","}}")


# ─── ENHANCED CLASSIFICATION PROMPT ─────────────────────────────────────────────

CLASSIFICATION_PROMPTT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
    """
You are an intent‐classification assistant.  Your goal is to assign the latest user message to exactly one of these labels:

  • import:  The user is asking to fill, review, or update an IMPORT declaration form.  
  • export:  The user is asking to fill, review, or update an EXPORT declaration form.  
  • normal: Any other conversation — e.g. greetings, regulatory questions, clarifications, unrelated topics, or discussion of documents without requesting form‐filling.  

Use the full chat history, the new message, and any document text to decide.  If unsure, default to 'normal'  
Respond with exactly one word (import, export, or normal) and nothing else.
=== Chat History ===
{{history}}

=== Document Context ===
{{documents}}
""",
        ),
        ("human", "{input}"),
    ]
)

CLASSIFICATION_PROMPT = PromptTemplate(
    input_variables=["history", "input", "documents"],
    template=f"""
You are an intent‐classification assistant.  Your goal is to assign the latest user message to exactly one of these labels:

  • import:  The user is asking to fill, review, or update an IMPORT declaration form.  
  • export:  The user is asking to fill, review, or update an EXPORT declaration form.  
  • normal: Any other conversation — e.g. greetings, regulatory questions, clarifications, unrelated topics, or discussion of documents without requesting form‐filling.  

Use the full chat history, the new message, and any document text to decide.  If unsure, default to 'normal'  
Respond with exactly one word (import, export, or normal) and nothing else.

=== Chat History ===
{{history}}

=== New User Message ===
{{input}}

=== Document Context ===
{{documents}}
"""
)


# ─── REVISED NORMAL-CHAT PROMPT ─────────────────────────────────────────────────
NORMAL_PROMPT = PromptTemplate(
    input_variables=["history", "input", "documents"],
    template=f"""
You are an expert Australian Customs and Border Protection regulations assistant.  Your task is to:

1. Provide clear, accurate guidance on import/export rules, required forms, duties, restrictions, and compliance under Australian law.  
2. Leverage any supplied document excerpts and the conversation history and any document inside the history to inform your answer.  
3. If the user greets you, reply politely and ask how you can assist with import/export regulations or form-filling.  
4. If the user’s question is unrelated to import/export regulations (or is offensive), apologize briefly and ask if they need help with Australian import/export requirements or filling a declaration form.  
5. If the user requests form-filling here, remind them to use the form-filling workflow or upload the necessary documents.  
6. If the user refers to missing or incomplete documents, prompt them to upload or clarify what’s needed.  

Always respond in a professional, helpful tone and focus solely on Australian import/export guidance.

=== Chat History ===
{{history}}

=== User Message ===
{{input}}

=== Extracted Documents ===
{{documents}}
"""
)


# ---Import and Export Prompt Templates ---
IMPORT_GUIDE_PATH = ROOT / "docs" / "import_guide_2.txt"
EXPORT_GUIDE_PATH = ROOT / "docs" / "export_guide_2.txt"

with open(IMPORT_GUIDE_PATH, 'r', encoding='utf-8') as f:
    IMPORT_GUIDE_TEXT = f.read()[:2000] + "... [truncated] ..."
with open(EXPORT_GUIDE_PATH, 'r', encoding='utf-8') as f:
    EXPORT_GUIDE_TEXT = f.read()[:2000] + "... [truncated] ..."


IMPORT_PROMPTT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a customs declaration assistant specializing in Australian import declarations (B650/N10 forms). 

Your task is to extract information from the provided documents and chat history to fill out the import declaration schema.

Chat history:

{{history}}

Use the following reference guide to fill the form

{IMPORT_GUIDE_TEXT}
User input and document content:
{{input}}

IMPORTANT INSTRUCTIONS:
1. Analyze the provided documents and chat history carefully
2. Extract relevant information for the import declaration
3. Output ONLY a valid JSON object that matches this exact schema structure:
{B650_SAMPLE_JSON}

SCHEMA REQUIREMENTS:
- The JSON must have exactly these top-level keys: "header", "air_transport_lines", "sea_transport_lines", "tariff_lines"
- "header" contains import declaration metadata
- "air_transport_lines" is an array of air transport details (use if air freight)
- "sea_transport_lines" is an array of sea transport details (use if sea freight)  
- "tariff_lines" is an array of goods/tariff information
- Use null for any fields where information is not available
- Follow the validation guidelines that are provided with the schema
- Ensure all required fields are filled based on the schema



Output ONLY the JSON object - no explanations, no markdown formatting.
Return only the json object.
Strictly do not include any backticks like ``` or keyword json in your response.
"""
        ),
        ("human", "{input}"),
    ]
)


IMPORT_PROMPT = PromptTemplate(
    input_variables=["history", "input"],
    template=f"""
You are a customs declaration assistant specializing in Australian import declarations (B650/N10 forms). 

Your task is to extract information from the provided documents and chat history to fill out the import declaration schema.

Chat history:

{{history}}

Use the following reference guide to fill the form

{IMPORT_GUIDE_TEXT}
User input and document content:
{{input}}

IMPORTANT INSTRUCTIONS:
1. Analyze the provided documents and chat history carefully
2. Extract relevant information for the import declaration
3. Output ONLY a valid JSON object that matches this exact schema structure:
{B650_SAMPLE_JSON}

SCHEMA REQUIREMENTS:
- The JSON must have exactly these top-level keys: "header", "air_transport_lines", "sea_transport_lines", "tariff_lines"
- "header" contains import declaration metadata
- "air_transport_lines" is an array of air transport details (use if air freight)
- "sea_transport_lines" is an array of sea transport details (use if sea freight)  
- "tariff_lines" is an array of goods/tariff information
- Use null for any fields where information is not available
- Follow the validation guidelines that are provided with the schema
- Ensure all required fields are filled based on the schema



Output ONLY the JSON object - no explanations, no markdown formatting.
Return only the json object.
Strictly do not include any backticks like ``` or keyword json in your response.
"""
)

EXPORT_PROMPT = PromptTemplate(
    input_variables=["history", "input"],
    template=f"""
You are a customs declaration assistant specializing in Australian export declarations (B957 forms).

Your task is to extract information from the provided documents and chat history to fill out the export declaration schema.

Chat history:
{{history}}

Use the following reference guide to fill the form

{EXPORT_GUIDE_TEXT}

User input and document content:
{{input}}

IMPORTANT INSTRUCTIONS:
1. Analyze the provided documents and chat history carefully
2. Extract relevant information for the export declaration
3. Output ONLY a valid JSON object that matches this exact schema structure:
{B957_SAMPLE_JSON}

SCHEMA REQUIREMENTS:
- The JSON must be a flat structure with all fields at the top level
- All required fields must be filled based on the schema
- Use null for any optional fields where information is not available
- Follow the exact field names and data types specified in the schema



Output ONLY the JSON object - no explanations, no markdown formatting.
Return only the json object.
Strictly do not include any backticks like ``` or keyword json in your response.
"""
)

# --- Memory ---
def get_memory():
    return ConversationBufferMemory(memory_key="history", input_key="input")

# --- LLMChain Constructors ---
def get_import_chain(llm):
    #import_message = IMPORT_PROMPTT.format({"IMPORT_GUIDE_TEXT":IMPORT_GUIDE_TEXT, "B650_SAMPLE_JSON":B650_SAMPLE_JSON, "input":input, "history":history}])
    print('import_chain returned')
    # print('IMPORT_PROMPTT', IMPORT_PROMPTT)
    chain = IMPORT_PROMPT | llm
    # print('chain', chain)
    return chain

def get_export_chain(llm):
    return LLMChain(
        llm=llm,
        prompt=EXPORT_PROMPT
    )

def get_classification_chain(llm):
    # return LLMChain(
    #     llm=llm,
    #     prompt=CLASSIFICATION_PROMPT
    # )
    chain = CLASSIFICATION_PROMPTT | llm
    return chain

def get_normal_chain(llm):
    return LLMChain(
        llm=llm,
        prompt=NORMAL_PROMPT
    )

# --- Workflow Selector ---
def get_chain(form_type: str, llm):
    print(f"Selecting chain for form type: {form_type}")
    if form_type.lower() in ["import", "b650", "n10"]:
        return get_import_chain(llm)
    elif form_type.lower() in ["export", "b957"]:
        return get_export_chain(llm)
    elif form_type.lower() in ["classification"]:
        return get_classification_chain(llm)
    else:
        return get_normal_chain(llm)