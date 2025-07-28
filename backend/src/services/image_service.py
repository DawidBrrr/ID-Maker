import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from ..FastCropper.image_processing import process_image
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
            
            # Przetwarzaj obraz używając FastCropper
            process_image(
                image_path=filepath,
                error_folder=error_folder,
                output_folder=output_folder,
                debug_output=error_folder,
                res_x=params['res_x'],
                res_y=params['res_y'],
                top_margin_value=params['top_margin_value'],
                bottom_margin_value=params['bottom_margin_value'],
                left_right_margin_value=params['left_right_margin_value'],
                naming_config={
                    "prefix": "", 
                    "name": "", 
                    "numbering_type": "", 
                    "extension": "Bez zmian"
                },
                image_count=1
            )
            
            # Znajdź najnowszy plik wyjściowy
            output_filename = file_service.get_latest_output_file(session_id)
            
            if output_filename:
                # Sukces
                task_service.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED, 
                    result_file=output_filename
                )
                logger.info(f"Image processing completed for task {task_id}")
            else:
                # Brak pliku wyjściowego
                task_service.update_task_status(
                    task_id, 
                    TaskStatus.FAILED, 
                    error_message="Nie znaleziono pliku wyjściowego"
                )
                logger.error(f"No output file found for task {task_id}")
                
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