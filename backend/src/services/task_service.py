import threading
from typing import Dict, Optional
from datetime import datetime, timedelta

from ..models.task import Task, TaskStatus
from ..utils.exceptions import TaskNotFoundException
from ..config import config

class TaskService:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
    
    def create_task(self, session_id: str, filename: str, document_type: str) -> Task:
        """Tworzy nowy task"""
        task = Task(
            session_id=session_id,
            filename=filename,
            document_type=document_type,
            status=TaskStatus.PENDING
        )
        
        with self.lock:
            self.tasks[task.id] = task
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Pobiera task po ID"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          error_message: Optional[str] = None, 
                          result_file: Optional[str] = None) -> bool:
        """Aktualizuje status taska"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            
            task.update_status(status, error_message)
            if result_file:
                task.result_file = result_file
            
            return True
    
    def cleanup_old_tasks(self, hours: int = None):
        """Usuwa stare taski"""
        hours = hours or config.SESSION_TIMEOUT_HOURS
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            expired_tasks = [
                task_id for task_id, task in self.tasks.items()
                if task.created_at < cutoff_time
            ]
            
            for task_id in expired_tasks:
                del self.tasks[task_id]
        
        return len(expired_tasks)
    
    def get_session_tasks(self, session_id: str) -> list[Task]:
        """Pobiera wszystkie taski dla sesji"""
        with self.lock:
            return [task for task in self.tasks.values() if task.session_id == session_id]

# Singleton instance
task_service = TaskService()