from functools import wraps
from flask import request, jsonify, g
import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
import redis
import json
import logging

from ..config import config

logger = logging.getLogger(__name__)

class RateLimiter:
    """Zaawansowany rate limiter z różnymi strategiami"""
    
    def __init__(self, use_redis: bool = False):
        self.use_redis = use_redis
        self.memory_storage: Dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()
        
        # Redis connection (optional)
        self.redis_client = None
        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    db=0, 
                    decode_responses=True
                )
                self.redis_client.ping()  # Test connection
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using memory storage.")
                self.use_redis = False
    
    def _get_client_identifier(self, request) -> str:
        """Pobiera identyfikator klienta"""
        # Priorytet: user_id > API key > IP
        if hasattr(g, 'user_id') and g.user_id:
            return f"user:{g.user_id}"
        
        if hasattr(g, 'api_key') and g.api_key:
            return f"api:{g.api_key}"
        
        # IP address (uwzględniając proxy)
        client_ip = (
            request.environ.get('HTTP_X_FORWARDED_FOR', '') or
            request.environ.get('HTTP_X_REAL_IP', '') or
            request.remote_addr or 'unknown'
        )
        
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        return f"ip:{client_ip}"
    
    def _check_rate_limit_memory(self, key: str, max_requests: int, 
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
    
    def _check_rate_limit_redis(self, key: str, max_requests: int, 
                               window_seconds: int) -> Tuple[bool, Dict]:
        """Sprawdza rate limit w Redis (sliding window)"""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        pipe = self.redis_client.pipeline()
        
        # Usuń stare entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Policz current requests
        pipe.zcard(key)
        
        # Dodaj current request
        pipe.zadd(key, {f"{current_time}:{time.time_ns()}": current_time})
        
        # Ustaw expiry
        pipe.expire(key, window_seconds + 1)
        
        results = pipe.execute()
        current_requests = results[1]
        
        if current_requests >= max_requests:
            # Pobierz najstarszy request dla retry_after
            oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
            oldest_time = oldest[0][1] if oldest else current_time
            retry_after = int(oldest_time + window_seconds - current_time)
            
            # Usuń dodany request (przekroczono limit)
            self.redis_client.zrem(key, f"{current_time}:{time.time_ns()}")
            
            return False, {
                'current_requests': current_requests,
                'max_requests': max_requests,
                'retry_after': max(retry_after, 1),
                'window_seconds': window_seconds
            }
        
        return True, {
            'current_requests': current_requests + 1,
            'max_requests': max_requests,
            'retry_after': 0,
            'window_seconds': window_seconds
        }
    
    def check_rate_limit(self, key: str, max_requests: int, 
                        window_seconds: int) -> Tuple[bool, Dict]:
        """Główna metoda sprawdzania rate limit"""
        try:
            if self.use_redis and self.redis_client:
                return self._check_rate_limit_redis(key, max_requests, window_seconds)
            else:
                return self._check_rate_limit_memory(key, max_requests, window_seconds)
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fallback - pozwól na request
            return True, {
                'current_requests': 0,
                'max_requests': max_requests,
                'retry_after': 0,
                'window_seconds': window_seconds,
                'error': str(e)
            }
    
    def get_rate_limit_status(self, key: str, window_seconds: int) -> Dict:
        """Pobiera status rate limit dla klucza"""
        try:
            if self.use_redis and self.redis_client:
                current_time = time.time()
                window_start = current_time - window_seconds
                
                # Usuń stare entries i policz current
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                results = pipe.execute()
                
                return {
                    'current_requests': results[1],
                    'window_seconds': window_seconds,
                    'storage': 'redis'
                }
            else:
                current_time = time.time()
                window_start = current_time - window_seconds
                
                with self.lock:
                    # Usuń stare requesty
                    while (self.memory_storage[key] and 
                           self.memory_storage[key][0] < window_start):
                        self.memory_storage[key].popleft()
                    
                    return {
                        'current_requests': len(self.memory_storage[key]),
                        'window_seconds': window_seconds,
                        'storage': 'memory'
                    }
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {'error': str(e)}
    
    def reset_rate_limit(self, key: str) -> bool:
        """Resetuje rate limit dla klucza (admin function)"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
            else:
                with self.lock:
                    if key in self.memory_storage:
                        del self.memory_storage[key]
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

# Singleton instance
rate_limiter = RateLimiter()

def advanced_rate_limit(max_requests: int = None, window_minutes: int = 1, 
                       per_user: bool = False, burst_allowance: int = 0):
    """Zaawansowany rate limiting decorator"""
    max_requests = max_requests or config.RATE_LIMIT_PER_MINUTE
    window_seconds = window_minutes * 60
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_id = rate_limiter._get_client_identifier(request)
            
            # Different limits for different client types
            if per_user and client_id.startswith('user:'):
                # Registered users get higher limits
                effective_max = max_requests * 2
            elif client_id.startswith('api:'):
                # API key users get even higher limits
                effective_max = max_requests * 5
            else:
                # Anonymous users get base limit
                effective_max = max_requests
            
            # Add burst allowance
            effective_max += burst_allowance
            
            # Check rate limit
            allowed, info = rate_limiter.check_rate_limit(
                client_id, effective_max, window_seconds
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
    """Circuit breaker pattern dla rate limitera"""
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