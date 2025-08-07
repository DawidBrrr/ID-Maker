from functools import wraps
from flask import request, jsonify
import time
import threading
from collections import defaultdict, deque
from typing import Dict, Tuple
import logging

from ..config import config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Prosty rate limiter bazujący na IP"""
    
    def __init__(self):
        self.memory_storage: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
    
    def _get_client_identifier(self, request) -> str:
        """Pobiera IP klienta"""
        client_ip = (
            request.environ.get('HTTP_X_FORWARDED_FOR', '') or
            request.environ.get('HTTP_X_REAL_IP', '') or
            request.remote_addr or 'unknown'
        )
        
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        return f"ip:{client_ip}"
    
    def check_rate_limit(self, key: str, max_requests: int, 
                        window_seconds: int) -> Tuple[bool, Dict]:
        """Sprawdza rate limit w pamięci"""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        with self.lock:
            # Usuń stare requesty
            while (self.memory_storage[key] and 
                   self.memory_storage[key][0] < window_start):
                self.memory_storage[key].popleft()
            
            # Sprawdź limit
            current_requests = len(self.memory_storage[key])
            
            if current_requests >= max_requests:
                # Oblicz retry_after
                oldest_request = self.memory_storage[key][0] if self.memory_storage[key] else current_time
                retry_after = int(oldest_request + window_seconds - current_time)
                
                return False, {
                    'current_requests': current_requests,
                    'max_requests': max_requests,
                    'retry_after': max(retry_after, 1),
                    'window_seconds': window_seconds
                }
            
            # Dodaj current request
            self.memory_storage[key].append(current_time)
            
            return True, {
                'current_requests': current_requests + 1,
                'max_requests': max_requests,
                'retry_after': 0,
                'window_seconds': window_seconds
            }

# Singleton instance
rate_limiter = RateLimiter()

def advanced_rate_limit(max_requests: int = None, window_minutes: int = 1, 
                       per_user: bool = False, burst_allowance: int = 0):
    """Rate limiting decorator"""
    max_requests = max_requests or config.RATE_LIMIT_PER_MINUTE
    window_seconds = window_minutes * 60
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = rate_limiter._get_client_identifier(request)
            
            # Check rate limit
            allowed, info = rate_limiter.check_rate_limit(
                client_id, max_requests, window_seconds
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {client_id}: {info}")
                
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {info["max_requests"]} per {window_minutes} minutes',
                    'retry_after': info['retry_after'],
                    'current_requests': info['current_requests'],
                    'max_requests': info['max_requests']
                })
                
                # Add rate limit headers
                response.headers['X-RateLimit-Limit'] = str(info['max_requests'])
                response.headers['X-RateLimit-Remaining'] = str(max(0, info['max_requests'] - info['current_requests']))
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + info['retry_after']))
                response.headers['Retry-After'] = str(info['retry_after'])
                
                return response, 429
            
            # Add rate limit info to response headers
            def add_rate_limit_headers(response):
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(info['max_requests'])
                    response.headers['X-RateLimit-Remaining'] = str(max(0, info['max_requests'] - info['current_requests']))
                    response.headers['X-RateLimit-Reset'] = str(int(time.time() + window_seconds))
                return response
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Add headers to response
            if isinstance(result, tuple):
                response, status_code = result
                return add_rate_limit_headers(response), status_code
            else:
                return add_rate_limit_headers(result)
        
        return decorated_function
    return decorator

def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """Circuit breaker pattern"""
    failure_count = defaultdict(int)
    last_failure_time = defaultdict(float)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = rate_limiter._get_client_identifier(request)
            current_time = time.time()
            
            # Check if circuit is open
            if (failure_count[client_id] >= failure_threshold and
                current_time - last_failure_time[client_id] < recovery_timeout):
                
                return jsonify({
                    'error': 'Service temporarily unavailable',
                    'message': 'Too many failures. Please try again later.',
                    'retry_after': int(recovery_timeout - (current_time - last_failure_time[client_id]))
                }), 503
            
            try:
                result = f(*args, **kwargs)
                
                # Reset failure count on success
                failure_count[client_id] = 0
                
                return result
                
            except Exception as e:
                # Increment failure count
                failure_count[client_id] += 1
                last_failure_time[client_id] = current_time
                
                logger.error(f"Circuit breaker recorded failure for {client_id}: {e}")
                raise
        
        return decorated_function
    return decorator