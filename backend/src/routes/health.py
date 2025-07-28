from flask import Blueprint, jsonify
import os
import psutil
from datetime import datetime

from ..config import config
from ..services.task_service import task_service

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Sprawdź podstawowe funkcje
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "checks": {
                "folders": check_folders(),
                "memory": check_memory(),
                "tasks": check_tasks()
            }
        }
        
        # Sprawdź czy wszystkie sprawdzenia przeszły
        all_healthy = all(check["status"] == "ok" for check in health_status["checks"].values())
        
        if not all_healthy:
            health_status["status"] = "degraded"
            return jsonify(health_status), 503
        
        return jsonify(health_status)
    
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@health_bp.route('/metrics')
def metrics():
    """Endpoint z metrykami"""
    try:
        return jsonify({
            "active_tasks": len([t for t in task_service.tasks.values() if t.status.value == "processing"]),
            "total_tasks": len(task_service.tasks),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "uptime": get_uptime()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def check_folders():
    """Sprawdza czy foldery są dostępne"""
    try:
        for folder in [config.upload_folder, config.output_folder, config.error_folder]:
            if not os.path.exists(folder):
                return {"status": "error", "message": f"Folder {folder} does not exist"}
            if not os.access(folder, os.W_OK):
                return {"status": "error", "message": f"Folder {folder} is not writable"}
        
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_memory():
    """Sprawdza użycie pamięci"""
    try:
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            return {"status": "warning", "usage": f"{memory.percent}%"}
        return {"status": "ok", "usage": f"{memory.percent}%"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_tasks():
    """Sprawdza status tasków"""
    try:
        total_tasks = len(task_service.tasks)
        processing_tasks = len([t for t in task_service.tasks.values() if t.status.value == "processing"])
        
        return {
            "status": "ok",
            "total": total_tasks,
            "processing": processing_tasks
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_uptime():
    """Zwraca uptime aplikacji"""
    try:
        import time
        return time.time() - psutil.Process().create_time()
    except:
        return 0