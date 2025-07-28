from functools import wraps
from flask import request, jsonify, g
import jwt
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
import logging

from ..config import config

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """Middleware do autoryzacji i autentykacji"""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def generate_api_key(self, user_id: str, permissions: list = None) -> str:
        """Generuje API key dla użytkownika"""
        permissions = permissions or ['upload', 'status', 'download']
        
        # Prosty API key based on user_id i timestamp
        timestamp = str(int(time.time()))
        data = f"{user_id}:{timestamp}:{config.SECRET_KEY}"
        api_key = hashlib.sha256(data.encode()).hexdigest()[:32]
        
        self.api_keys[api_key] = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': timestamp,
            'last_used': timestamp
        }
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Waliduje API key"""
        if not api_key or api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        # Sprawdź wygaśnięcie (7 dni)
        created_at = int(key_data['created_at'])
        if time.time() - created_at > 7 * 24 * 3600:
            del self.api_keys[api_key]
            return None
        
        # Aktualizuj last_used
        key_data['last_used'] = str(int(time.time()))
        
        return key_data
    
    def create_session_token(self, session_id: str, user_data: Dict[str, Any] = None) -> str:
        """Tworzy JWT token dla sesji"""
        user_data = user_data or {}
        
        payload = {
            'session_id': session_id,
            'user_data': user_data,
            'iat': int(time.time()),
            'exp': int(time.time()) + (24 * 3600)  # 24h expiry
        }
        
        token = jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
        
        # Zapisz sesję
        self.sessions[session_id] = {
            'token': token,
            'created_at': time.time(),
            'user_data': user_data
        }
        
        return token
    
    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Waliduje JWT token"""
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            session_id = payload.get('session_id')
            
            if session_id and session_id in self.sessions:
                return payload
            
            return None
            
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def cleanup_expired_sessions(self):
        """Usuwa wygasłe sesje"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['created_at'] > 24 * 3600:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Singleton instance
auth_middleware = AuthMiddleware()

def require_api_key(permissions: list = None):
    """Decorator wymagający API key"""
    permissions = permissions or []
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Pobierz API key z headerów
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                api_key = request.args.get('api_key')  # Fallback z query params
            
            if not api_key:
                return jsonify({'error': 'API key required'}), 401
            
            # Waliduj API key
            key_data = auth_middleware.validate_api_key(api_key)
            if not key_data:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Sprawdź uprawnienia
            user_permissions = key_data.get('permissions', [])
            if permissions and not any(perm in user_permissions for perm in permissions):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Dodaj dane użytkownika do g
            g.user_id = key_data['user_id']
            g.permissions = user_permissions
            g.api_key = api_key
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_session_token(f):
    """Decorator wymagający session token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Pobierz token z headerów
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Session token required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Waliduj token
        payload = auth_middleware.validate_session_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Dodaj dane sesji do g
        g.session_id = payload['session_id']
        g.user_data = payload.get('user_data', {})
        g.token = token
        
        return f(*args, **kwargs)
    return decorated_function

def optional_auth(f):
    """Decorator z opcjonalną autoryzacją"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Sprawdź API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            key_data = auth_middleware.validate_api_key(api_key)
            if key_data:
                g.user_id = key_data['user_id']
                g.permissions = key_data.get('permissions', [])
                g.authenticated = True
                return f(*args, **kwargs)
        
        # Sprawdź session token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = auth_middleware.validate_session_token(token)
            if payload:
                g.session_id = payload['session_id']
                g.user_data = payload.get('user_data', {})
                g.authenticated = True
                return f(*args, **kwargs)
        
        # Brak autoryzacji - ustaw domyślne wartości
        g.authenticated = False
        g.user_id = None
        g.permissions = []
        
        return f(*args, **kwargs)
    return decorated_function

def verify_signature(f):
    """Decorator weryfikujący podpis requestu (webhook security)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get('X-Signature-256')
        if not signature:
            return jsonify({'error': 'Missing signature'}), 401
        
        # Pobierz payload
        payload = request.get_data()
        
        # Oblicz expected signature
        expected_signature = hmac.new(
            config.SECRET_KEY.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Porównaj podpisy (secure comparison)
        if not hmac.compare_digest(f"sha256={expected_signature}", signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        return f(*args, **kwargs)
    return decorated_function