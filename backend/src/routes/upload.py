from flask import Blueprint, request, jsonify
import uuid
import logging
from ..config import config
from ..utils.decorators import rate_limit, validate_session, log_request, handle_errors
from ..services.file_service import file_service
from ..services.image_service import image_service
from ..services.task_service import task_service
from ..utils.exceptions import ValidationException
from ..middleware.auth import require_api_key, optional_auth
from ..middleware.rate_limiter import advanced_rate_limit, circuit_breaker

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/hello')
@log_request
def hello():
    return jsonify({"message": "Skadruj portret!"})

@upload_bp.route('/upload', methods=['POST'])
@rate_limit(max_requests=5, window_minutes=1)  # Bardziej restrykcyjny limit dla uploadu
@log_request
@handle_errors
def upload_file():
    # Pobierz lub wygeneruj session_id
    session_id = request.form.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Sprawdź czy plik został przesłany
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    try:
        # Zapisz plik
        filepath = file_service.save_uploaded_file(file, session_id)
        logger.info(f"File saved: {filepath}")
        
        # Pobierz typ dokumentu
        document_type = request.form.get("document_type", "id_card")
        
        # Pobierz parametry przetwarzania
        try:
            params = config.DOCUMENT_TYPES.get(document_type, {})
        except ImportError:
            # Fallback parameters
            params = {
                "res_x": 492,
                "res_y": 633,
                "top_margin_value": 0.3,
                "bottom_margin_value": 0.4,
                "left_right_margin_value": 0.0
            }
        
        # Stwórz task
        task = task_service.create_task(session_id, file.filename, document_type)
        
        # Rozpocznij przetwarzanie
        image_service.process_image_async(task, filepath, params)
        
        return jsonify({
            "message": "Rozpoczęto przetwarzanie",
            "task_id": task.id,
            "session_id": session_id
        })
        
    except ValidationException as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({"error": "Upload failed"}), 500