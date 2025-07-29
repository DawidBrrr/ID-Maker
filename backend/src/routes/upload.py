from flask import Blueprint, request, jsonify, g
import json
import uuid
import logging
import shutil
import os
from ..config import config
from ..utils.decorators import log_request, handle_errors
from ..utils.helpers import clear_client_data
from ..services.file_service import file_service
from ..services.image_service import image_service
from ..services.task_service import task_service
from ..utils.exceptions import ValidationException
from ..middleware.auth import require_api_key, optional_auth
from ..middleware.rate_limiter import advanced_rate_limit, circuit_breaker

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/hello')
@advanced_rate_limit(max_requests=30, window_minutes=1)
@optional_auth
@log_request
@handle_errors
def hello():
    user_info = {}
    if g.get('authenticated', False):
        if g.get('user_id'):
            user_info['user_id'] = g.user_id
        if g.get('permissions'):
            user_info['permissions'] = g.permissions
    
    return jsonify({
        "message": "Skadruj portret!",
        **user_info
    })

@upload_bp.route('/upload', methods=['POST'])
@advanced_rate_limit(max_requests=10, window_minutes=1, per_user=True, burst_allowance=2)
@circuit_breaker(failure_threshold=3, recovery_timeout=60)
@optional_auth  # Opcjonalna autoryzacja - działa bez i z kluczem API
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
        logger.info(f"File saved: {filepath} for user: {g.get('user_id', 'anonymous')}")
        
        # Pobierz typ dokumentu
        document_type = request.form.get("document_type", "id_card")
        
        # Pobierz parametry przetwarzania
        try:
            params = config.DOCUMENT_TYPES.get(document_type, {})
        except AttributeError:
            # Fallback parameters
            params = {
                "res_x": 492,
                "res_y": 633,
                "top_margin_value": 0.3,
                "bottom_margin_value": 0.4,
                "left_right_margin_value": 0.0
            }
        
        # Stwórz task z informacją o użytkowniku
        task = task_service.create_task(
            session_id=session_id, 
            filename=file.filename, 
            document_type=document_type,
            user_id=g.get('user_id'),  # Dodaj user_id jeśli dostępne
            authenticated=g.get('authenticated', False)
        )
        
        # Rozpocznij przetwarzanie
        image_service.process_image_async(task, filepath, params)
        
        response_data = {
            "message": "Rozpoczęto przetwarzanie",
            "task_id": task.id,
            "session_id": session_id
        }
        
        # Dodaj informacje dla uwierzytelnionych użytkowników
        if g.get('authenticated', False):
            response_data["authenticated"] = True
            if g.get('user_id'):
                response_data["user_id"] = g.user_id
        
        return jsonify(response_data)
        
    except ValidationException as e:
        logger.warning(f"Validation error: {str(e)} for user: {g.get('user_id', 'anonymous')}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Upload error: {str(e)} for user: {g.get('user_id', 'anonymous')}", exc_info=True)
        return jsonify({"error": "Upload failed"}), 500
    

@upload_bp.route('/clear', methods=['POST'])
@advanced_rate_limit(max_requests=30, window_minutes=1)
@log_request
@handle_errors
def clear_data():
    session_id = None
    if request.is_json:
        session_id = request.json.get("session_id")
    else:
        import json
        try:
            data = json.loads(request.data)
            session_id = data.get("session_id")
        except Exception:
            pass
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    user_upload_folder = os.path.join(config.UPLOAD_FOLDER, session_id)
    user_output_folder = os.path.join(config.OUTPUT_FOLDER, session_id)
    user_error_folder = os.path.join(config.ERROR_FOLDER, session_id)
    clear_client_data(user_upload_folder, user_output_folder, user_error_folder)
    return jsonify({"message": "Data cleared"})