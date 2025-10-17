# ===============================
# 🐍 Base Image
# ===============================
FROM python:3.10-slim

# ===============================
# 📂 Set Working Directory
# ===============================
WORKDIR /app

# ===============================
# 🧩 Install Dependencies
# ===============================
COPY requirements.txt .
RUN pip install spacy
RUN python -m spacy download en_core_web_sm
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# ===============================
# 📦 Copy Application Files
# ===============================
COPY . .

# ===============================
# 🌐 Expose Port
# ===============================
EXPOSE 8000

# ===============================
# 🚀 Start FastAPI using Uvicorn
# ===============================
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
