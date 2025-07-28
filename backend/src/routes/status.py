from flask import Blueprint, jsonify

from ..utils.decorators import rate_limit, log_request, handle_errors
from ..services.task_service import task_service
from ..utils.exceptions import TaskNotFoundException

status_bp = Blueprint('status', __name__)

@status_bp.route('/status/<task_id>')
@rate_limit(max_requests=60, window_minutes=1)  # Wyższy limit dla statusu
@log_request
@handle_errors
def check_status(task_id):
    task = task_service.get_task(task_id)
    
    if not task:
        return jsonify({"error": "Invalid task_id"}), 404
    
    response_data = task.to_dict()
    
    # Dodaj URL do pliku jeśli gotowy
    if task.result_file:
        response_data['cropped_file_url'] = f"/api/output/{task.session_id}/{task.result_file}"
    
    return jsonify(response_data)
