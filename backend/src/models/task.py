from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filename: Optional[str] = None
    error_message: Optional[str] = None
    result_file: Optional[str] = None
    document_type: str = "id_card"
    
    def update_status(self, status: TaskStatus, error_message: Optional[str] = None):
        self.status = status
        self.updated_at = datetime.now()
        if error_message:
            self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'filename': self.filename,
            'error_message': self.error_message,
            'result_file': self.result_file,
            'document_type': self.document_type
        }