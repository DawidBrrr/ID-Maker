from flask import Blueprint, send_from_directory, jsonify, request
import os
import logging
import json

from ..config import config
from ..utils.decorators import rate_limit, log_request, handle_errors
from ..utils.helpers import clear_client_data
from ..services.file_service import file_service
from ..services.task_service import task_service
from ..utils.validators import sanitize_filename

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__)

@files_bp.route('/output/<session_id>/<filename>')
@rate_limit(max_requests=200, window_minutes=1)
@log_request
@handle_errors
def serve_output_file(session_id, filename):
    """Służy pliki wyjściowe"""
    # Sanityzuj parametry
    session_id = sanitize_filename(session_id)
    filename = sanitize_filename(filename)
    
    # Sprawdź czy plik istnieje
    if not file_service.file_exists(session_id, filename, 'output'):
        return jsonify({"error": "File not found"}), 404
    
    # Pobierz ścieżkę do folderu output
    _, output_folder, _ = file_service.get_user_folders(session_id)
    
    logger.info(f"Serving file {filename} from session {session_id}")
    
    return send_from_directory(
        output_folder, 
        filename, 
        as_attachment=True,
        mimetype='application/octet-stream'
    )

@files_bp.route('/clear', methods=['POST'])
@rate_limit(max_requests=30, window_minutes=1)
@log_request
@handle_errors
def clear_data():
    """Czyści dane sesji"""
    session_id = None
    
    # Obsługa różnych formatów wejścia (JSON, form, raw)
    if request.is_json:
        session_id = request.json.get("session_id")
    else:
        try:
            data = json.loads(request.data)
            session_id = data.get("session_id")
        except Exception:
            session_id = request.form.get("session_id")
    
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    # Czyszczenie folderów uploads, output, errors
    user_upload_folder = os.path.join(config.UPLOAD_FOLDER, session_id)
    user_output_folder = os.path.join(config.OUTPUT_FOLDER, session_id)
    user_error_folder = os.path.join(config.ERROR_FOLDER, session_id)
    
    clear_client_data(user_upload_folder, user_output_folder, user_error_folder)

    # Usuń także taski z tej sesji
    task_service.clear_session_tasks(session_id)
    logger.info(f"Cleared data for session: {session_id}")
    
    return jsonify({"message": "Data cleared", "session_id": session_id})

@files_bp.route('/list/<session_id>')
@rate_limit(max_requests=60, window_minutes=1)
@log_request
@handle_errors
def list_session_files(session_id):
    """Lista plików w sesji"""
    session_id = sanitize_filename(session_id)
    
    try:
        upload_folder, output_folder, error_folder = file_service.get_user_folders(session_id)
        
        files_info = {
            "session_id": session_id,
            "upload_files": [],
            "output_files": [],
            "error_files": []
        }
        
        # Lista plików upload
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                filepath = os.path.join(upload_folder, filename)
                if os.path.isfile(filepath):
                    files_info["upload_files"].append({
                        "filename": filename,
                        "size": os.path.getsize(filepath),
                        "modified": os.path.getmtime(filepath)
                    })
        
        # Lista plików output
        if os.path.exists(output_folder):
            for filename in os.listdir(output_folder):
                filepath = os.path.join(output_folder, filename)
                if os.path.isfile(filepath):
                    files_info["output_files"].append({
                        "filename": filename,
                        "size": os.path.getsize(filepath),
                        "modified": os.path.getmtime(filepath),
                        "download_url": f"/api/files/output/{session_id}/{filename}"
                    })
        
        # Lista plików error
        if os.path.exists(error_folder):
            for filename in os.listdir(error_folder):
                filepath = os.path.join(error_folder, filename)
                if os.path.isfile(filepath):
                    files_info["error_files"].append({
                        "filename": filename,
                        "size": os.path.getsize(filepath),
                        "modified": os.path.getmtime(filepath)
                    })
        
        return jsonify(files_info)
        
    except Exception as e:
        logger.error(f"Failed to list files for session {session_id}: {str(e)}")
        return jsonify({"error": "Failed to list files"}), 500