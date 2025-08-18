from flask import Blueprint, jsonify

from ..utils.decorators import rate_limit, log_request, handle_errors
from ..services.task_service import task_service

status_bp = Blueprint('status', __name__)

@status_bp.route('/status/<task_id>')
@rate_limit(max_requests=120, window_minutes=1)
@log_request
@handle_errors
def check_status(task_id):
    task = task_service.get_task(task_id)

    if not task:
        return jsonify({"error": "Invalid task_id", "status": "error"}), 404
    
    response_data = task.to_dict()
    # Add URL to the file if ready
    if task.result_file:
        response_data['cropped_file_url'] = f"/api/output/{task.session_id}/{task.result_file}"
        response_data['status'] = "done"
    else:
        response_data['status'] = "processing"

    return jsonify(response_data)

@status_bp.route('/status/session/<session_id>')
@rate_limit(max_requests=60, window_minutes=1)
@log_request
@handle_errors
def get_session_tasks(session_id):
    """Endpoint to fetch all tasks in a session"""

    try:
        session_tasks = task_service.get_session_tasks(session_id)

        tasks_data = []
        for task in session_tasks:
            task_data = task.to_dict()
            if task.result_file:
                task_data['cropped_file_url'] = f"/api/output/{task.session_id}/{task.result_file}"
                task_data['status'] = "done"
            else:
                task_data['status'] = "processing"
            tasks_data.append(task_data)

        return jsonify({
            "session_id": session_id,
            "total_tasks": len(tasks_data),
            "tasks": tasks_data
        })

    except Exception as e:
        return jsonify({"error": f"Failed to get session tasks: {str(e)}", "status": "error"}), 500