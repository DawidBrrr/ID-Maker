from flask import Blueprint, jsonify, g

from ..middleware.auth import optional_auth
from ..middleware.rate_limiter import advanced_rate_limit
from ..utils.decorators import log_request, handle_errors
from ..services.task_service import task_service
from ..utils.exceptions import TaskNotFoundException

status_bp = Blueprint('status', __name__)

@status_bp.route('/status/<task_id>')
@advanced_rate_limit(max_requests=120, window_minutes=1, per_user=True)  # Wyższy limit dla statusu
@optional_auth
@log_request
@handle_errors
def check_status(task_id):
    task = task_service.get_task(task_id)
    
    if not task:
        return jsonify({"error": "Invalid task_id"}), 404
    
    # Sprawdź uprawnienia - użytkownicy mogą sprawdzać tylko swoje taski
    if g.get('authenticated', False) and g.get('user_id'):
        if task.user_id and task.user_id != g.user_id:
            return jsonify({"error": "Access denied"}), 403
    
    response_data = task.to_dict()
    
    # Dodaj URL do pliku jeśli gotowy
    if task.result_file:
        response_data['cropped_file_url'] = f"/api/files/output/{task.session_id}/{task.result_file}"
    
    # Dodaj dodatkowe informacje dla uwierzytelnionych użytkowników
    if g.get('authenticated', False):
        response_data['authenticated'] = True
        if hasattr(task, 'premium') and task.premium:
            response_data['premium_task'] = True
    
    return jsonify(response_data)

@status_bp.route('/status/user/<user_id>')
@advanced_rate_limit(max_requests=30, window_minutes=1, per_user=True)
@optional_auth  # Sprawdzimy uprawnienia wewnątrz
@log_request
@handle_errors
def get_user_tasks(user_id):
    """Endpoint do pobierania wszystkich tasków użytkownika"""
    
    # Sprawdź uprawnienia
    if not g.get('authenticated', False):
        return jsonify({"error": "Authentication required"}), 401
    
    # Użytkownicy mogą sprawdzać tylko swoje taski (chyba że mają admin permissions)
    if g.get('user_id') != user_id and 'admin' not in g.get('permissions', []):
        return jsonify({"error": "Access denied"}), 403
    
    try:
        user_tasks = task_service.get_user_tasks(user_id)
        
        tasks_data = []
        for task in user_tasks:
            task_data = task.to_dict()
            if task.result_file:
                task_data['cropped_file_url'] = f"/api/files/output/{task.session_id}/{task.result_file}"
            tasks_data.append(task_data)
        
        return jsonify({
            "user_id": user_id,
            "total_tasks": len(tasks_data),
            "tasks": tasks_data
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user tasks: {str(e)}"}), 500

@status_bp.route('/status/session/<session_id>')
@advanced_rate_limit(max_requests=60, window_minutes=1)
@optional_auth
@log_request
@handle_errors
def get_session_tasks(session_id):
    """Endpoint do pobierania wszystkich tasków w sesji"""
    
    try:
        session_tasks = task_service.get_session_tasks(session_id)
        
        tasks_data = []
        for task in session_tasks:
            # Sprawdź uprawnienia dla każdego taska
            if g.get('authenticated', False) and g.get('user_id'):
                if task.user_id and task.user_id != g.user_id:
                    continue  # Pomiń taski innych użytkowników
            
            task_data = task.to_dict()
            if task.result_file:
                task_data['cropped_file_url'] = f"/api/files/output/{task.session_id}/{task.result_file}"
            tasks_data.append(task_data)
        
        return jsonify({
            "session_id": session_id,
            "total_tasks": len(tasks_data),
            "tasks": tasks_data,
            "authenticated": g.get('authenticated', False)
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get session tasks: {str(e)}"}), 500