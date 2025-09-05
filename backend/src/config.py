import os
from dataclasses import dataclass, field
from typing import Set

@dataclass
class Config:
    # Basic configuration
    #Change to False in production
    DEBUG: bool = True
    
    # Folders
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_FOLDER: str = os.path.join(BASE_DIR, 'Data')
    UPLOAD_FOLDER = os.path.join(DATA_FOLDER, 'uploads')
    OUTPUT_FOLDER = os.path.join(DATA_FOLDER, 'output')
    ERROR_FOLDER = os.path.join(DATA_FOLDER, 'errors')
    
    # Limity
    MAX_CONTENT_LENGTH: int = 25 * 1024 * 1024  # 25MB
    MAX_FILES_PER_SESSION: int = 10
    SESSION_TIMEOUT_HOURS: int = 24
    MAX_FILE_AGE_HOURS: int = 12
    
    # Threading
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv('RATE_LIMIT', '30'))
    
    # Allowed file types
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {'.jpg', '.jpeg', '.png', '.webp'})
    ALLOWED_MIME_TYPES: set = field(default_factory=lambda: {
        'image/jpeg', 'image/png', 'image/webp', 'image/jpg'
    })
    
    # Allowed document types
    ALLOWED_DOCUMENT_TYPES: set = field(default_factory=lambda: frozenset({'id_card', 'passport'}))

    # Document processing parameters
    DOCUMENT_TYPES: dict = field(default_factory=lambda: {
        "passport": {
            "res_x": 768,
            "res_y": 1004,
            "top_margin_value": 0.3,
            "bottom_margin_value": 0.4,
            "left_right_margin_value": 0,
        },
        "id_card": {
            "res_x": 492,
            "res_y": 633,
            "top_margin_value": 0.3,
            "bottom_margin_value": 0.4,
            "left_right_margin_value": 0,
        }
    })
    
    @property
    def upload_folder(self) -> str:
        path = os.path.join(self.DATA_FOLDER, 'uploads')
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def output_folder(self) -> str:
        path = os.path.join(self.DATA_FOLDER, 'output')
        os.makedirs(path, exist_ok=True)
        return path
    
    @property
    def error_folder(self) -> str:
        path = os.path.join(self.DATA_FOLDER, 'errors')
        os.makedirs(path, exist_ok=True)
        return path

config = Config()