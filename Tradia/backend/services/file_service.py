import os
import shutil
from typing import List, Optional
from fastapi import UploadFile
from config.settings import settings
import uuid


class FileService:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.storage_type = settings.storage_type
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_file(self, file: UploadFile, user_id: str = "default") -> str:
        """Save uploaded file to storage"""
        try:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
            
            # Create user-specific directory
            user_dir = os.path.join(self.upload_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Full file path
            file_path = os.path.join(user_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            return file_path
            
        except Exception as e:
            print(f"File save error: {e}")
            raise
    
    async def save_files(self, files: List[UploadFile], user_id: str = "default") -> List[str]:
        """Save multiple uploaded files"""
        saved_paths = []
        
        for file in files:
            try:
                file_path = await self.save_file(file, user_id)
                saved_paths.append(file_path)
            except Exception as e:
                print(f"Failed to save file {file.filename}: {e}")
                continue
        
        return saved_paths
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"File deletion error: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get file information"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                "path": file_path,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime
            }
        except Exception as e:
            print(f"File info error: {e}")
            return None
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Clean up old temporary files"""
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned_count = 0
        
        try:
            for root, dirs, files in os.walk(self.upload_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                        except Exception:
                            continue
            
            return cleaned_count
            
        except Exception as e:
            print(f"File cleanup error: {e}")
            return 0


# Global instance
file_service = FileService()
