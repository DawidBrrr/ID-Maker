from functools import wraps
from flask import request, jsonify, g
import time
from collections import defaultdict, deque
from threading import Lock
import logging

from ..config import config
from .validators import validate_session_id

# Rate limiting storage
rate_limit_storage = defaultdict(deque)
rate_limit_lock = Lock()

logger = logging.getLogger(__name__)

def rate_limit(max_requests: int = None, window_minutes: int = 1):
    """Rate limiting decorator"""
    max_requests = max_requests or config.RATE_LIMIT_PER_MINUTE
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Pobierz IP klienta (uwzględniając proxy)
            client_ip = (request.environ.get('HTTP_X_FORWARDED_FOR', '') or 
                        request.environ.get('HTTP_X_REAL_IP', '') or 
                        request.remote_addr or 'unknown')
            
            # Jeśli jest za proxy, weź pierwszy IP
            if ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            current_time = time.time()
            window_start = current_time - (window_minutes * 60)
            
            with rate_limit_lock:
                # Usuń stare requesty
                while (rate_limit_storage[client_ip] and 
                       rate_limit_storage[client_ip][0] < window_start):
                    rate_limit_storage[client_ip].popleft()
                
                # Sprawdź limit
                if len(rate_limit_storage[client_ip]) >= max_requests:
                    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': int(window_minutes * 60),
                        'max_requests': max_requests,
                        'window_minutes': window_minutes
                    }), 429
                
                # Dodaj current request
                rate_limit_storage[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_session(required: bool = True):
    """Waliduje session_id z request"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            session_id = None
            
            # Sprawdź różne źródła session_id
            if request.method == 'POST':
                if request.is_json:
                    session_id = request.json.get('session_id')
                else:
                    session_id = request.form.get('session_id')
            elif request.method == 'GET':
                session_id = request.args.get('session_id')
            
            if required and (not session_id or not validate_session_id(session_id)):
                return jsonify({'error': 'Invalid or missing session_id'}), 400
            
            g.session_id = session_id
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_request(f):
    """Loguje szczegóły requestu"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(f"{request.method} {request.path} - {client_ip} - "
                       f"{result[1] if isinstance(result, tuple) else 200} - {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{request.method} {request.path} - {client_ip} - ERROR - {duration:.3f}s - {str(e)}")
            raise
    return decorated_function

def handle_errors(f):
    """Decorator do obsługi błędów"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({'error': str(e)}), 400
        except FileNotFoundError as e:
            logger.error(f"File not found in {f.__name__}: {str(e)}")
            return jsonify({'error': 'File not found'}), 404
        except PermissionError as e:
            logger.error(f"Permission error in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Permission denied'}), 403
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function