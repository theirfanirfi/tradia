# ===============================
# 🐍 Base Image
# ===============================
FROM python:3.10-slim

# ===============================
# 📂 Set Working Directory
# ===============================
WORKDIR /celeryapp

# ===============================
# 🧩 Install Dependencies
# ===============================

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && apt-get install -y \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*
RUN pip install spacy
RUN python -m spacy download en_core_web_sm
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install sentence_transformers
# RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# ===============================
# 📦 Copy Application Files
# ===============================
COPY . .
RUN pip install -r requirements.txt

# ===============================
# 🌐 Expose Port
# ===============================
# EXPOSE 8000

# ===============================
# 🚀 Start FastAPI using Uvicorn
# ===============================
CMD ["celery", "-A", "tasks.background_tasks", "worker"]
