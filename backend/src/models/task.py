import uuid
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    def __init__(self, session_id: str, filename: str, document_type: str = "id_card"):
        self.id = str(uuid.uuid4())
        self.session_id = session_id
        self.filename = filename
        self.document_type = document_type
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.result_file: Optional[str] = None
        self.error_message: Optional[str] = None
        self.processing_time: Optional[float] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.biometric_warnings: Optional[list] = None
        self.biometric_errors: Optional[list] = None
    
    def update_status(self, status: TaskStatus, error_message: Optional[str] = None, 
                     biometric_warnings: Optional[list] = None, biometric_errors: Optional[list] = None):
        """Aktualizuje status taska"""
        old_status = self.status
        self.status = status
        self.updated_at = datetime.now()
        
        if error_message:
            self.error_message = error_message
            
        if biometric_warnings:
            self.biometric_warnings = biometric_warnings
            
        if biometric_errors:
            self.biometric_errors = biometric_errors
        
        # Śledzenie czasów
        if status == TaskStatus.PROCESSING and old_status == TaskStatus.PENDING:
            self.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and self.started_at:
            self.completed_at = datetime.now()
            self.processing_time = (self.completed_at - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje task do dict"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "filename": self.filename,
            "document_type": self.document_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time": self.processing_time,
            "result_file": self.result_file,
            "error_message": self.error_message,
            "biometric_warnings": self.biometric_warnings,
            "biometric_errors": self.biometric_errors
        }
    
    def __repr__(self):
        return f"<Task {self.id} - {self.status.value} - {self.filename}>"