from flask import Blueprint, send_from_directory, jsonify, request, g
import os
import logging

from ..config import config
from ..middleware.auth import optional_auth, require_api_key
from ..middleware.rate_limiter import advanced_rate_limit
from ..utils.decorators import log_request, handle_errors
from ..services.file_service import file_service
from ..services.task_service import task_service
from ..utils.validators import sanitize_filename

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__)

@files_bp.route('/output/<session_id>/<filename>')
@advanced_rate_limit(max_requests=200, window_minutes=1, per_user=True)
@optional_auth
@log_request
@handle_errors
def serve_output_file(session_id, filename):
    """Służy pliki wyjściowe z opcjonalną autoryzacją"""
    # Sanityzuj parametry
    session_id = sanitize_filename(session_id)
    filename = sanitize_filename(filename)
    
    # Sprawdź czy plik istnieje
    if not file_service.file_exists(session_id, filename, 'output'):
        return jsonify({"error": "File not found"}), 404
    
    # Sprawdź uprawnienia do pliku jeśli użytkownik jest uwierzytelniony
    if g.get('authenticated', False) and g.get('user_id'):
        # Znajdź task związany z tym plikiem
        session_tasks = task_service.get_session_tasks(session_id)
        file_task = None
        for task in session_tasks:
            if task.result_file == filename:
                file_task = task
                break
        
        # Jeśli task ma user_id i nie pasuje do obecnego użytkownika
        if file_task and file_task.user_id and file_task.user_id != g.user_id:
            # Sprawdź czy ma uprawnienia admin
            if 'admin' not in g.get('permissions', []):
                return jsonify({"error": "Access denied"}), 403
    
    # Pobierz ścieżkę do folderu output
    _, output_folder, _ = file_service.get_user_folders(session_id)
    
    logger.info(f"Serving file {filename} from session {session_id} to user {g.get('user_id', 'anonymous')}")
    
    return send_from_directory(
        output_folder, 
        filename, 
        as_attachment=True,
        mimetype='application/octet-stream'
    )

@files_bp.route('/clear', methods=['POST'])
@advanced_rate_limit(max_requests=20, window_minutes=1, per_user=True)
@optional_auth
@log_request
@handle_errors
def clear_data():
    """Czyści dane sesji z opcjonalną autoryzacją"""
    session_id = request.json.get("session_id") if request.is_json else request.form.get("session_id")
    
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    
    # Sprawdź uprawnienia jeśli użytkownik jest uwierzytelniony
    if g.get('authenticated', False) and g.get('user_id'):
        # Sprawdź czy użytkownik ma taski w tej sesji
        session_tasks = task_service.get_session_tasks(session_id)
        user_has_tasks = any(
            task.user_id == g.user_id for task in session_tasks 
            if hasattr(task, 'user_id') and task.user_id
        )
        
        # Jeśli nie ma tasków w sesji i nie ma uprawnień admin
        if not user_has_tasks and 'admin' not in g.get('permissions', []):
            return jsonify({"error": "Access denied to this session"}), 403
    
    success = file_service.clear_session_data(session_id)
    
    if success:
        # Usuń także taski z tej sesji
        task_service.clear_session_tasks(session_id)
        
        logger.info(f"Cleared data for session: {session_id} by user: {g.get('user_id', 'anonymous')}")
        return jsonify({"message": "Data cleared", "session_id": session_id})
    else:
        return jsonify({"error": "Failed to clear data"}), 500

@files_bp.route('/clear-user', methods=['POST'])
@advanced_rate_limit(max_requests=10, window_minutes=1, per_user=True)
@require_api_key(permissions=['upload', 'admin'])  # Wymaga API key z uprawnieniami admin
@log_request
@handle_errors
def clear_user_data():
    """Czyści wszystkie dane użytkownika - wymaga uprawnień admin"""
    user_id = request.json.get("user_id") if request.is_json else request.form.get("user_id")
    
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400
    
    # Dodatowa kontrola uprawnień
    if 'admin' not in g.get('permissions', []):
        return jsonify({"error": "Admin permissions required"}), 403
    
    try:
        # Znajdź wszystkie taski użytkownika
        user_tasks = task_service.get_user_tasks(user_id)
        sessions_to_clear = set()
        
        for task in user_tasks:
            sessions_to_clear.add(task.session_id)
        
        cleared_sessions = 0
        for session_id in sessions_to_clear:
            if file_service.clear_session_data(session_id):
                cleared_sessions += 1
        
        # Usuń taski użytkownika
        cleared_tasks = task_service.clear_user_tasks(user_id)
        
        logger.info(f"Admin {g.user_id} cleared data for user {user_id}: {cleared_sessions} sessions, {cleared_tasks} tasks")
        
        return jsonify({
            "message": "User data cleared",
            "user_id": user_id,
            "cleared_sessions": cleared_sessions,
            "cleared_tasks": cleared_tasks
        })
        
    except Exception as e:
        logger.error(f"Failed to clear user data: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to clear user data"}), 500

@files_bp.route('/list/<session_id>')
@advanced_rate_limit(max_requests=60, window_minutes=1, per_user=True)
@optional_auth
@log_request
@handle_errors
def list_session_files(session_id):
    """Lista plików w sesji"""
    session_id = sanitize_filename(session_id)
    
    # Sprawdź uprawnienia jeśli użytkownik jest uwierzytelniony
    if g.get('authenticated', False) and g.get('user_id'):
        session_tasks = task_service.get_session_tasks(session_id)
        user_has_tasks = any(
            task.user_id == g.user_id for task in session_tasks 
            if hasattr(task, 'user_id') and task.user_id
        )
        
        if not user_has_tasks and 'admin' not in g.get('permissions', []):
            return jsonify({"error": "Access denied to this session"}), 403
    
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
        
        # Lista plików error (tylko dla uwierzytelnionych użytkowników)
        if g.get('authenticated', False) and os.path.exists(error_folder):
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