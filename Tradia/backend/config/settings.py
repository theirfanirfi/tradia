from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:tradia1234@localhost:5432/tradia_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    jwt_secret: str = "mysecretkey"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: 60
    refresh_token_expire_days: int = 30
    
    # File Storage
    storage_type: str = "local"  # local or s3
    upload_dir: str = "./uploads"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None

    # Ollama
    ollama_url: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    embed_model: str = os.getenv("EMBED_MODEL", "mxbai-embed-large:latest")

    # LLM (served elsewhere via LLMService)
    llm_model: str = os.getenv("LLM_MODEL", "llama2")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY","")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL","")
    
    # OCR
    ocr_engine: str = "tesseract"  # tesseract or textract
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001","http://3.27.231.129:3000", "http://localhost:60146","http://127.0.0.1:60146","http://3.27.231.129"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
