# Australian Customs Declaration Backend

A FastAPI backend for processing Australian import/export declarations using OCR, LLM, and automated PDF generation.

## Features

- **Document Processing**: Upload invoices and documents for automated processing
- **OCR Extraction**: Extract text from PDFs and images using Tesseract
- **LLM Processing**: Use OpenAI GPT-4 to understand and structure document content
- **Real-time Updates**: WebSocket-based status updates during processing
- **PDF Generation**: Automatically generate official declaration forms
- **Background Tasks**: Celery-based asynchronous document processing
- **Data Validation**: Comprehensive input validation and sanitization

## Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Primary database with SQLAlchemy ORM
- **Redis**: Message broker for Celery and caching
- **Celery**: Background task processing
- **Tesseract**: OCR engine for text extraction
- **OpenAI GPT-4**: LLM for document understanding
- **ReportLab**: PDF generation
- **WebSockets**: Real-time status updates

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Tesseract OCR

### Setup

1. **Clone and navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb customs_db
   
   # Update DATABASE_URL in .env
   DATABASE_URL=postgresql://user:password@localhost:5432/customs_db
   ```

6. **Start Redis**
   ```bash
   redis-server
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/customs_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `STORAGE_TYPE` | File storage type (`local` or `s3`) | `local` |
| `UPLOAD_DIR` | Local upload directory | `./uploads` |
| `OPENAI_API_KEY` | OpenAI API key for LLM processing | None |
| `OCR_ENGINE` | OCR engine (`tesseract` or `textract`) | `tesseract` |

### OCR Setup

**Tesseract Installation:**
- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Running the Application

### Development Mode

1. **Start the FastAPI server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Celery worker**
   ```bash
   celery -A tasks.background_tasks worker --loglevel=info
   ```

3. **Start Celery beat (optional, for scheduled tasks)**
   ```bash
   celery -A tasks.background_tasks beat --loglevel=info
   ```

### Production Mode

```bash
# Build and run with Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Endpoints

### Process Management
- `POST /api/process/create` - Create new declaration process
- `GET /api/process/{process_id}` - Get process details
- `GET /api/process/{process_id}/status` - Get process status
- `GET /api/process/` - List all processes

### Document Management
- `POST /api/documents/upload/{process_id}` - Upload documents
- `GET /api/documents/{process_id}` - Get process documents
- `DELETE /api/documents/{document_id}` - Delete document

### Items Management
- `GET /api/items/{process_id}` - Get extracted items
- `PUT /api/items/{item_id}` - Update item details
- `DELETE /api/items/{item_id}` - Delete item

### Declaration Management
- `GET /api/declaration/{process_id}` - Get declaration data
- `PUT /api/declaration/{process_id}/update` - Update declaration fields
- `POST /api/declaration/{process_id}/generate-pdf` - Generate final PDF

### WebSocket
- `ws://localhost:8000/ws/process/{process_id}` - Real-time status updates

## Database Schema

The system uses the following main tables:

- **user_process**: Process tracking and status
- **user_declaration**: Declaration data and schemas
- **user_documents**: Document storage and metadata
- **user_process_items**: Extracted items from documents

## Background Processing

Document processing follows this workflow:

1. **Upload**: Files are saved and document records created
2. **Extracting**: OCR extracts text from documents
3. **Understanding**: LLM processes text to extract structured data
4. **Generating**: Items are extracted and stored
5. **Done**: Process completes with extracted data

## File Storage

- **Local Storage**: Files stored in `UPLOAD_DIR` with user-specific subdirectories
- **S3 Storage**: AWS S3 integration for cloud storage (configure via environment variables)

## Security Features

- Input validation and sanitization
- File type and size validation
- CORS configuration
- Rate limiting (can be added)
- Authentication ready (JWT implementation ready)

## Monitoring and Logging

- Process status tracking
- Progress calculation
- Error handling and logging
- Health check endpoints

## Development

### Adding New Services

1. Create service class in `services/` directory
2. Implement required methods
3. Add to `services/__init__.py`
4. Import and use in API endpoints

### Adding New API Endpoints

1. Create router in `api/` directory
2. Define endpoints with proper validation
3. Add to `api/__init__.py`
4. Include in `main.py`

### Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app tests/
```

## Troubleshooting

### Common Issues

1. **OCR not working**: Ensure Tesseract is installed and in PATH
2. **Database connection**: Check PostgreSQL is running and credentials are correct
3. **Redis connection**: Verify Redis server is running
4. **File uploads**: Check upload directory permissions

### Logs

Check application logs for detailed error information:
```bash
tail -f logs/app.log
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

This project is licensed under the MIT License.
