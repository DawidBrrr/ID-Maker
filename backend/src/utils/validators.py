import os
import re
import uuid
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage
from PIL import Image
from ..config import config
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    print("python-magic not installed. File type detection will be limited.")

from ..config import config

def validate_file(file: FileStorage, max_size: int = None) -> Tuple[bool, Optional[str]]:
    """Waliduje przesłany plik"""
    
    if not file or not file.filename:
        return False, "Brak pliku"
    
    max_size = max_size or config.MAX_CONTENT_LENGTH
    
    # Sprawdź rozmiar
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > max_size:
        return False, f"Plik za duży. Maksymalny rozmiar: {max_size/1024/1024:.1f}MB"
    
    if size == 0:
        return False, "Plik jest pusty"
    
    # Sprawdź rozszerzenie
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in config.ALLOWED_EXTENSIONS):
        return False, f"Niedozwolone rozszerzenie. Dozwolone: {', '.join(config.ALLOWED_EXTENSIONS)}"
    
    # Sprawdź MIME type (jeśli python-magic dostępne)
    if HAS_MAGIC:
        file_header = file.read(2048)
        file.seek(0)
        
        mime_type = magic.from_buffer(file_header, mime=True)
        if mime_type not in config.ALLOWED_MIME_TYPES:
            return False, f"Niedozwolony typ pliku: {mime_type}"
    
    # Sprawdź czy da się otworzyć jako obraz
    try:
        with Image.open(file) as img:
            # Sprawdź podstawowe parametry obrazu
            if img.width < 50 or img.height < 50:
                return False, "Obraz za mały (min. 50x50px)"
            if img.width > 10000 or img.height > 10000:
                return False, "Obraz za duży (max. 10000x10000px)"
            
            # Verify sprawdza integralność bez ładowania całego obrazu
            img.verify()
        file.seek(0)  # Reset po verify
    except Exception as e:
        return False, f"Uszkodzony plik obrazu: {str(e)}"
    
    return True, None

def validate_document_type(document_type: str) -> bool:
    """Waliduje typ dokumentu"""
    try:
        return document_type in config.ALLOWED_DOCUMENT_TYPES
    except ImportError:
        # Fallback jeśli constants nie istnieje
        return document_type in ['id_card', 'passport']

def sanitize_filename(filename: str) -> str:
    """Sanityzuje nazwę pliku"""
    # Usuń ścieżki
    filename = os.path.basename(filename)
    
    # Usuń niebezpieczne znaki, zostaw tylko alfanumeryczne, kropki, myślniki i podkreślenia
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Usuń wielokrotne kropki (path traversal protection)
    filename = re.sub(r'\.{2,}', '.', filename)
    
    # Ogranicz długość
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    
    # Upewnij się że nie jest pusty
    if not filename or filename.startswith('.'):
        filename = f"file_{uuid.uuid4().hex[:8]}" + (os.path.splitext(filename)[1] if '.' in filename else '.jpg')
    
    return filename

def validate_session_id(session_id: str) -> bool:
    """Waliduje session ID"""
    if not session_id:
        return False
    
    # Sprawdź długość i format (UUID-like)
    if len(session_id) < 10 or len(session_id) > 50:
        return False
    
    # Sprawdź czy zawiera tylko bezpieczne znaki
    if not re.match(r'^[a-zA-Z0-9\-]+$', session_id):
        return False
    
    return True