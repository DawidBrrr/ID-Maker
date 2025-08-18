import os
import shutil
import glob
import time
from typing import Optional
from werkzeug.datastructures import FileStorage

from ..config import config
from ..utils.validators import sanitize_filename, validate_file
from ..utils.exceptions import ValidationException

class FileService:
    def __init__(self):
        pass
    
    def get_user_folders(self, session_id: str) -> tuple[str, str, str]:
        """Zwraca ścieżki do folderów użytkownika"""
        upload_folder = os.path.join(config.upload_folder, session_id)
        output_folder = os.path.join(config.output_folder, session_id)
        error_folder = os.path.join(config.error_folder, session_id)
        
        # Stwórz foldery jeśli nie istnieją
        for folder in [upload_folder, output_folder, error_folder]:
            if not os.path.exists(folder):  # Sprawdź, czy folder istnieje
                os.makedirs(folder, exist_ok=True)
        
        return upload_folder, output_folder, error_folder
    
    def save_uploaded_file(self, file: FileStorage, session_id: str, max_files_override: Optional[int] = None) -> str:
        """Zapisuje przesłany plik"""
        # Walidacja
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            raise ValidationException(error_msg)
        
        # Sprawdź limit plików na sesję
        upload_folder, _, _ = self.get_user_folders(session_id)
        existing_files = len(os.listdir(upload_folder))
        
        max_files = max_files_override or config.MAX_FILES_PER_SESSION
        if existing_files >= max_files:
            raise ValidationException(f"Przekroczony limit plików na sesję ({max_files})")
        
        # Sanityzuj nazwę pliku
        safe_filename = sanitize_filename(file.filename)
        
        # Dodaj timestamp jeśli plik już istnieje
        filepath = os.path.join(upload_folder, safe_filename)
        if os.path.exists(filepath):
            name, ext = os.path.splitext(safe_filename)
            timestamp = int(time.time())
            safe_filename = f"{name}_{timestamp}{ext}"
            filepath = os.path.join(upload_folder, safe_filename)
        
        # Zapisz plik
        file.save(filepath)
        
        return filepath
    
    def get_latest_output_file(self, session_id: str) -> Optional[str]:
        """Zwraca najnowszy plik wyjściowy"""
        _, output_folder, _ = self.get_user_folders(session_id)
        
        files = glob.glob(os.path.join(output_folder, '*'))
        if not files:
            return None
        
        latest_file = max(files, key=os.path.getctime)
        return os.path.basename(latest_file)
    
    def clear_session_data(self, session_id: str) -> bool:
        """Usuwa wszystkie pliki sesji"""
        try:
            upload_folder, output_folder, error_folder = self.get_user_folders(session_id)
            
            for folder in [upload_folder, output_folder, error_folder]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
            
            return True
        except Exception as e:
            print(f"Error clearing session data: {e}")
            return False
    
    def file_exists(self, session_id: str, filename: str, folder_type: str = 'output') -> bool:
        """Sprawdza czy plik istnieje"""
        upload_folder, output_folder, error_folder = self.get_user_folders(session_id)
        
        folder_map = {
            'upload': upload_folder,
            'output': output_folder,
            'error': error_folder
        }
        
        folder = folder_map.get(folder_type, output_folder)
        filepath = os.path.join(folder, filename)
        
        return os.path.exists(filepath) and os.path.isfile(filepath)
    
    def get_file_info(self, session_id: str, filename: str, folder_type: str = 'output') -> Optional[dict]:
        """Zwraca informacje o pliku"""
        if not self.file_exists(session_id, filename, folder_type):
            return None
        
        upload_folder, output_folder, error_folder = self.get_user_folders(session_id)
        folder_map = {
            'upload': upload_folder,
            'output': output_folder,
            'error': error_folder
        }
        
        folder = folder_map.get(folder_type, output_folder)
        filepath = os.path.join(folder, filename)
        
        try:
            stat = os.stat(filepath)
            return {
                'filename': filename,
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'folder_type': folder_type
            }
        except OSError:
            return None

# Singleton instance
file_service = FileService()