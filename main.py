from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import shutil
import json
from core.ocr_extractor import extract_text_from_file
import asyncio
from core.langchain_logic import get_chain
from dotenv import load_dotenv
from langchain.output_parsers import PydanticOutputParser
from typing import Type
import subprocess
import boto3
from botocore.client import Config
from forms_schema.b650_schema import B650Model
from langchain_community.chat_models import ChatOpenAI
from loguru import logger
from testingcustomfile import tradiaLLM
from ATradiaLLM import atradiaLLM


# B650_parser = PydanticOutputParser(pydantic_object=B650Model)
# B650_SAMPLE_PATH = os.path.join(os.path.dirname(__file__), 'forms_schema', 'b650_sample.json')
# with open(B650_SAMPLE_PATH, 'r') as f:
#     B650_SAMPLE_JSON = f.read()
# B957_SAMPLE_PATH = os.path.join(os.path.dirname(__file__), 'forms_schema', 'b957_sample.json')
# with open(B957_SAMPLE_PATH, 'r') as f:
#     B957_SAMPLE_JSON = f.read()
load_dotenv()

app = FastAPI()

# during development, allow the React dev server
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://13.54.43.232"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # <-- allow React dev origin
    allow_credentials=True,           # <-- if you're sending cookies/auth
    allow_methods=["*"],              # <-- allow all HTTP methods (GET, POST, OPTIONS…)
    allow_headers=["*"],              # <-- allow all headers (including x-api-key)
)

TEMPLATE = {
    "import": "b650_unlocked.pdf",
    "export": "b957_unlocked.pdf"
}

# TODO: llm to pdf mapping for export is missing
MAPPING = {
    "import": "b650_llm_to_pdf_field_map.json",
    "export": "b957_llm_to_pdf_field_map.json"
}

# Base directory for storing conversations
BASE_DIR = os.path.join(os.getcwd(), "conversations")
os.makedirs(BASE_DIR, exist_ok=True)

# ENDPOINT_ID = os.getenv("ENDPOINT_ID")
ENDPOINT_ID = "ex6feyp44b7orz"
# BASE_URL    = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/openai/v1"
BASE_URL    = f"https://api.runpod.ai/v2/ex6feyp44b7orz/openai/v1//chat/completions"
# MODEL_NAME = os.getenv("MODEL_NAME")
MODEL_NAME = "qwen2-7b-instruct"
API_KEY     = os.getenv("RUNPOD_API_KEY") # API key for LLM hosted on Runpod
API_KEY_SECRET = os.getenv("API_KEY_SECRET") # API key for this chat API
if not API_KEY:
    raise ValueError("Please set the RUNPOD_API_KEY environment variable")
print(f"Using RunPod endpoint: {ENDPOINT_ID} with model: {MODEL_NAME} {BASE_URL}")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,  # <--- replace with your actual bucket's region
    config=Config(signature_version="s3v4")
)

# now create your LLM just like before, but override the OpenAI base URL
llm = ChatOpenAI(
    temperature=0.2,
    model_name=MODEL_NAME,
    openai_api_key=API_KEY,
    openai_api_base=BASE_URL,       # ← point at RunPod
    # ← you're using an OpenAI-compatible endpoint
)


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "backend/forms_schema"

B650_SAMPLE_PATH = os.path.join(SCHEMA_DIR, 'b650_sample.json')
with open(B650_SAMPLE_PATH, 'r') as f:
    B650_SAMPLE_JSON = f.read().replace("{","{{").replace("}","}}")

IMPORT_GUIDE_PATH = ROOT / "backend/docs" / "import_guide_2.txt"
EXPORT_GUIDE_PATH = ROOT / "backend/docs" / "export_guide_2.txt"

with open(IMPORT_GUIDE_PATH, 'r', encoding='utf-8') as f:
    IMPORT_GUIDE_TEXT = f.read()[:2000] + "... [truncated] ..."
with open(EXPORT_GUIDE_PATH, 'r', encoding='utf-8') as f:
    EXPORT_GUIDE_TEXT = f.read()[:2000] + "... [truncated] ..."


@app.post("/chat")
async def chat(
    request: Request,
    prompt: str = Form(...),
    conversation_id: str = Form(None),
    files: list[UploadFile] = File(default=[])
):
    # API key check
    api_key=API_KEY_SECRET
    # api_key = request.headers.get("x-api-key")
    if not api_key or api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # Validate file count
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed per request")

    # Determine conversation ID
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    
    # Create conversation directory if new
    convo_dir = os.path.join(BASE_DIR, conversation_id)
    os.makedirs(convo_dir, exist_ok=True)

    # Save uploaded files and extract text
    saved_files = []
    ocr_texts = []
    for idx, upload in enumerate(files, start=1):
        filename = f"doc_{idx}_{upload.filename}"
        file_path = os.path.join(convo_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        saved_files.append(filename)
        # OCR extraction
        text = await extract_text_from_file(file_path)
        ocr_texts.append({"filename": filename, "text": text})

    # Concatenate all OCR text for LLM input
    all_ocr_text = "\n".join([f"Document {idx}: {f['text']}" for idx, f in enumerate(ocr_texts, 1)])

    # Load or init history.json
    history_path = os.path.join(convo_dir, "history.json")
    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    # Append user message (include OCR text for downstream processing)
    history.append({
        "role": "user",
        "content": prompt,
        "ocr": ocr_texts
    })

    # Use chat history as string for now
    chat_history = "\n".join([f'{msg["role"]}: {msg["content"]} \nAttached Documents: {msg.get("ocr")} \nParsed PDF Form: {msg.get("parsed_form")}' for msg in history if "content" in msg])
    # logger.info(f"Conversation ID: {conversation_id} \n{chat_history}")
    # ─── CLASSIFY USER INTENT ──────────────────────────────────────────────────
    classification_chain = get_chain("classification", tradiaLLM)
    intent = classification_chain.invoke({
        "history":chat_history,
        "input":prompt,
        "documents":all_ocr_text
    }
    )
    intent = intent.strip().lower()  # Normalize intent to lowercase
      # should be 'normal', 'import', or 'export'
    normal_response = None
    form_response = None
    filled_pdf_url = None
    parsed_form = None

    if intent == "normal":
        # ─── HANDLE NORMAL CHAT ────────────────────────────────────────────────
        normal_chain = get_chain("normal", llm, input, chat_history)
        logger.info(f"Conversation ID: {conversation_id} \n{chat_history}")
        normal_response = normal_chain.invoke({
            "history":chat_history,
            "input":prompt,
            "documents":all_ocr_text
        }) 
        print(normal_response)
        logger.info(f"Normal Response: {normal_response}")    
        return JSONResponse({
            "normal_response": normal_response,
        })  
    else:
        # ─── IMPORT/EXPORT FORM FILLING ────────────────────────────────────────
        form_type = intent  # either 'import' or 'export'
        try:
            # Provide better context to the LLM
            enhanced_input = f"""
            Form Type: {form_type.upper()}
            User Request: {prompt}

            Document Content:
            {all_ocr_text}

            Please extract the relevant information from the documents above and fill out the appropriate customs declaration form.
            """
            chain = get_chain(form_type, tradiaLLM)
            print(f"Using chain: invoking now")
            # async def run_async():
            #     return await chain.ainvoke({"history":chat_history, "input":enhanced_input, "IMPORT_GUIDE_TEXT": IMPORT_GUIDE_TEXT,"B650_SAMPLE_JSON": B650_SAMPLE_JSON})
            # # logger.info(f"Parsed Form: {parsed_form}")
            # parsed_form = await asyncio.run(run_async)
            parsed_form = await chain.ainvoke({
                "history": chat_history,
                "input": enhanced_input,
                "IMPORT_GUIDE_TEXT": IMPORT_GUIDE_TEXT,
                "B650_SAMPLE_JSON": B650_SAMPLE_JSON
            })
            print(f"Parsed Form: {parsed_form}")
            print(f"Parsed Form: my")

            # return JSONResponse({"Check": parsed_form})
            # Save LLM response JSON in conversation folder
            llm_response_path = os.path.join(convo_dir, "llm_response.json")
            try:
                # If parsed_form is a string, try to load as JSON, else save as is
                if isinstance(parsed_form, str):
                    try:
                        parsed_form_json = json.loads(parsed_form)
                    except Exception:
                        parsed_form_json = {"error": parsed_form}
                else:
                    parsed_form_json = parsed_form
                with open(llm_response_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_form_json, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.info(f"Conversation ID: {conversation_id} - Error saving LLM response JSON: {e}")

            # Trigger PDF filling script
            filled_pdf_path = os.path.join(convo_dir, f"{intent}_filled_form.pdf")
            if TEMPLATE.get(form_type):
                template_pdf = os.path.join(os.path.dirname(__file__), "docs", TEMPLATE[form_type])
            else:
                template_pdf = None
            
            if MAPPING.get(form_type):
                mapping_json = os.path.join(os.path.dirname(__file__), "forms_schema", MAPPING[form_type])
            else:
                mapping_json = None
            
            pdf_filled_error = None
            form_response = "An error occured. Please try again."
            if template_pdf is not None and mapping_json is not None:
                writeonpdf_script = os.path.join(os.path.dirname(__file__), "core", "writeonpdf.py")
                try:
                    result = subprocess.run([
                        "python3", writeonpdf_script,
                        template_pdf,
                        llm_response_path,
                        mapping_json,
                        filled_pdf_path
                    ], capture_output=True, text=True, check=True)

                    # the command succeeded (exit code 0)
                    print("=== STDOUT ===")
                    # print(result.stdout)
                    print("=== STDERR ===")
                    # print(result.stderr)

                    # Upload filled PDF to S3 and generate download URL
                    try:
                        s3_key = f"{conversation_id}_{intent}_filled_form.pdf"

                        s3_client.upload_file(filled_pdf_path, S3_BUCKET_NAME, s3_key)

                        # Generate a presigned GET URL for the filled_pdf_url
                        filled_pdf_url = s3_client.generate_presigned_url(
                            "get_object",
                            Params={"Bucket": S3_BUCKET_NAME, 
                                    "Key": s3_key,
                                    "ResponseContentDisposition": f'attachment; filename="{s3_key}"'
                                },
                            ExpiresIn=3600 * 24 * 7  # link valid for 7 days
                        )
                        form_response = (
                        f"The {form_type} declaration form is filled with the matching information "
                        "from attached documents. Please review and let me know if any changes or updates are required."
                        )
                    except Exception as e:
                        logger.info(f"Conversation ID: {conversation_id} - Error uploading to S3 or generating URL: {e}")
                except subprocess.CalledProcessError as e:
                    # normalize in case e.stdout or e.stderr is None
                    out = e.stdout or ""
                    err = e.stderr or ""
                    logger.error("PDF fill process failed (exit code %d)", e.returncode)
                    if out:
                        logger.error("=== PDF fill STDOUT ===\n%s", out)
                    if err:
                        logger.error("=== PDF fill STDERR ===\n%s", err)

                    # preserve both in your error variable
                    pdf_filled_error = out + ("\n" if out and err else "") + err
                    logger.info(f"Conversation ID: {conversation_id} - Error occured while filling the PDF {pdf_filled_error}")
            else:
                logger.info(f"Conversation ID: {conversation_id} - \
                            Error: Skipping the filling of PDF form. Either template PDF or mapping JSON file is missing")
        except Exception as e:
            # logger.info(f"Conversation ID: {conversation_id} LLM error: {e}")
            parsed_form = None
            form_response = "An error occured. Please try again."
            

    # Placeholder assistant response
    assistant_response = normal_response if normal_response is not None else form_response
    history.append({"role": "assistant", "content": assistant_response, "parsed_form": parsed_form})

    # Save updated history
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    # Return response (only conversation_id, parsed_form, and filled_pdf_url)
    return JSONResponse({
        "conversation_id": conversation_id,
        "assistant_response": assistant_response,
        "parsed_form": parsed_form,
        "filled_pdf_form_url": filled_pdf_url
    })

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}
