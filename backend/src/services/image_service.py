import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from ..IdMaker.id_maker import id_maker
from ..config import config
from ..models.task import Task, TaskStatus
from ..services.task_service import task_service
from ..services.file_service import file_service
from ..utils.exceptions import ImageProcessingException

logger = logging.getLogger(__name__)

class ImageProcessingService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
    
    def process_image_async(self, task: Task, filepath: str, processing_params: Dict[str, Any]):
        """Rozpoczyna asynchroniczne przetwarzanie obrazu"""
        future = self.executor.submit(
            self._process_image_task,
            task.id,
            task.session_id,
            filepath,
            processing_params
        )
        return future
    
    def _process_image_task(self, task_id: str, session_id: str, filepath: str, params: Dict[str, Any]):
        """Przetwarza obraz w tle"""
        try:
            # Aktualizuj status na "processing"
            task_service.update_task_status(task_id, TaskStatus.PROCESSING)
            
            # Pobierz foldery
            _, output_folder, error_folder = file_service.get_user_folders(session_id)
            
            logger.info(f"Starting image processing for task {task_id}")
            
            # Przetwarzaj obraz 
            
            processor = id_maker(upload_path=filepath,
                                 error_folder=error_folder,
                                output_folder=output_folder,
                                params=params)
            processor.process_image()
            
            # Pobierz informacje biometryczne
            biometric_info = processor.get_biometric_info()
            
            # Sprawdź czy kadrowanie się udało
            cropping_successful = getattr(processor, 'cropping_successful', False)
            
            # Kategoryzuj informacje biometryczne
            error_messages = []
            warning_messages = []
            
            if biometric_info:
                # Sprawdź czy to jest błąd krytyczny czy ostrzeżenie
                if any(keyword in biometric_info.lower() for keyword in [
                    "nie wykryto twarzy", 
                    "wykryto wiele twarzy", 
                    "brakujące cechy twarzy"
                ]):
                    error_messages.append(biometric_info)
                else:
                    warning_messages.append(biometric_info)
            
            # Znajdź najnowszy plik wyjściowy
            output_filename = file_service.get_latest_output_file(session_id)
            
            if output_filename and cropping_successful:
                # Sukces - plik istnieje i kadrowanie się udało
                task_service.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result_file=output_filename,
                    biometric_warnings=warning_messages if warning_messages else None,
                    biometric_errors=error_messages if error_messages else None
                )
                logger.info(f"Image processing completed for task {task_id}")
            else:
                # Błąd - brak pliku wyjściowego lub nieudane kadrowanie
                error_msg = "Nie udało się przetworzyć zdjęcia"
                if not cropping_successful:
                    error_msg += " - błąd podczas kadrowania"
                elif not output_filename:
                    error_msg += " - nie znaleziono pliku wyjściowego"
                
                # Dodaj informacje biometryczne do błędu jeśli istnieją
                if error_messages:
                    error_msg += f". {error_messages[0]}"
                
                task_service.update_task_status(
                    task_id, 
                    TaskStatus.FAILED, 
                    error_message=error_msg,
                    biometric_warnings=warning_messages if warning_messages else None,
                    biometric_errors=error_messages if error_messages else None
                )
                logger.error(f"Image processing failed for task {task_id}: {error_msg}")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Image processing failed for task {task_id}: {error_msg}", exc_info=True)
            
            task_service.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error_message=error_msg
            )
    
    def shutdown(self):
        """Zamyka thread pool"""
        self.executor.shutdown(wait=True)

# Singleton instance
image_service = ImageProcessingService()