from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import Dict

from config.settings import settings
from config.database import engine, Base
from api import process_router, documents_router, items_router, declarations_router
from utils.status_manager import get_process_summary

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Australian Customs Declaration API",
    description="API for processing import/export declarations with OCR and LLM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(process_router)
app.include_router(documents_router)
app.include_router(items_router)
app.include_router(declarations_router)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, process_id: str):
        await websocket.accept()
        self.active_connections[process_id] = websocket

    def disconnect(self, process_id: str):
        if process_id in self.active_connections:
            del self.active_connections[process_id]

    async def send_personal_message(self, message: str, process_id: str):
        if process_id in self.active_connections:
            await self.active_connections[process_id].send_text(message)

manager = ConnectionManager()


@app.websocket("/ws/process/{process_id}")
async def websocket_process_status(websocket: WebSocket, process_id: str):
    """WebSocket endpoint for real-time process status updates"""
    await manager.connect(websocket, process_id)
    
    try:
        while True:
            # Get current process status and progress
            summary = get_process_summary(process_id)
            
            if summary:
                await websocket.send_json({
                    "status": summary.get("status", "unknown"),
                    "progress": summary.get("progress", 0),
                    "message": f"Process is {summary.get('status', 'unknown')}"
                })
            
            # Wait before next update
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(process_id)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Australian Customs Declaration API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
