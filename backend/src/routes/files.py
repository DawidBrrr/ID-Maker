from flask import Blueprint, send_from_directory, jsonify, request
import os
import logging

from ..config import config
from ..utils.decorators import rate_limit, validate_session, log_request, handle_errors
from ..services.file_service import file_service
from ..utils.validators import sanitize_filename

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__)

@files_bp.route('/output/<session_id>/<filename>')
@rate_limit(max_requests=100, window_minutes=1)
@log_request
@handle_errors
def serve_output_file(session_id, filename):
    # Sanityzuj parametry
    session_id = sanitize_filename(session_id)
    filename = sanitize_filename(filename)
    
    # Sprawdź czy plik istnieje
    if not file_service.file_exists(session_id, filename, 'output'):
        return jsonify({"error": "File not found"}), 404
    
    # Pobierz ścieżkę do folderu output
    _, output_folder, _ = file_service.get_user_folders(session_id)
    
    return send_from_directory(
        output_folder, 
        filename, 
        as_attachment=True,
        mimetype='application/octet-stream'
    )

@files_bp.route('/clear', methods=['POST'])
@rate_limit(max_requests=10, window_minutes=1)
@validate_session(required=True)
@log_request
@handle_errors
def clear_data():
    session_id = request.json.get("session_id") if request.is_json else request.form.get("session_id")
    
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    
    success = file_service.clear_session_data(session_id)
    
    if success:
        logger.info(f"Cleared data for session: {session_id}")
        return jsonify({"message": "Data cleared"})
    else:
        return jsonify({"error": "Failed to clear data"}), 500