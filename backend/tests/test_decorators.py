import pytest
from unittest.mock import MagicMock, patch
from functools import wraps
from flask import Flask, request, jsonify, g
import time
from collections import defaultdict, deque
from threading import Lock
from src.utils.decorators import *

# Testy dla rate_limit
def test_rate_limit_allow_request():
    """Testuje czy normalne requesty są przepuszczane"""
    rate_limit_storage.clear()
    app = Flask(__name__)
    
    @app.route('/')
    @rate_limit(max_requests=2, window_minutes=1)
    def index():
        return "OK"
    
    with app.test_client() as client:
        # Pierwsze 2 requesty powinny przejść
        assert client.get('/').status_code == 200
        assert client.get('/').status_code == 200
        # Trzeci powinien zostać zablokowany
        response = client.get('/')
        assert response.status_code == 429
        assert b'Rate limit exceeded' in response.data

def test_rate_limit_window_reset():
    """Testuje resetowanie okna czasowego"""
    rate_limit_storage.clear()
    app = Flask(__name__)
    
    @app.route('/')
    @rate_limit(max_requests=1, window_minutes=1)  # Bardzo krótkie okno
    def index():
        return "OK"
    
    with app.test_client() as client:
        # Pierwszy request powinien przejść
        assert client.get('/').status_code == 200
        # Drugi powinien zostać zablokowany
        assert client.get('/').status_code == 429
        # Po czasie okna, request powinien znów przejść
        time.sleep(61)  # Czekamy aż okno się zresetuje
        assert client.get('/').status_code == 200

# Testy dla validate_session
def test_validate_session_required_valid():
    """Testuje walidację poprawnego session_id"""
    app = Flask(__name__)
    
    @app.route('/', methods=['GET', 'POST'])  # Dodajemy obsługę POST
    @validate_session(required=True)
    def index():
        return "OK"
    
    with app.test_client() as client:
        # Test GET z parametrem
        response = client.get('/?session_id=abc-123-xyz')
        assert response.status_code == 200
        
        # Test POST z form data
        response = client.post('/', data={'session_id': 'abc-123-xyz'})
        assert response.status_code == 200
        
        # Test POST z JSON
        response = client.post('/', json={'session_id': 'abc-123-xyz'})
        assert response.status_code == 200

def test_validate_session_required_invalid():
    """Testuje brak lub niepoprawne session_id gdy wymagane"""
    app = Flask(__name__)
    
    @app.route('/')
    @validate_session(required=True)
    def index():
        return "OK"
    
    with app.test_client() as client:
        # Brak session_id
        response = client.get('/')
        assert response.status_code == 400
        assert b'Invalid or missing session_id' in response.data
        
        # Niepoprawne session_id
        response = client.get('/?session_id=invalid!')
        assert response.status_code == 400

def test_validate_session_not_required():
    """Testuje opcjonalne session_id"""
    app = Flask(__name__)
    
    @app.route('/')
    @validate_session(required=False)
    def index():
        return "OK"
    
    with app.test_client() as client:
        # Brak session_id - powinno przejść
        assert client.get('/').status_code == 200
        
        # Poprawne session_id - powinno przejść
        assert client.get('/?session_id=abc-123-xyz').status_code == 200
        
        # Niepoprawne session_id - powinno przejść (bo nie required)
        assert client.get('/?session_id=invalid!').status_code == 200

# Testy dla log_request
@patch('logging.Logger.info')
def test_log_request_success(mock_log):
    """Testuje logowanie udanego requestu"""
    app = Flask(__name__)
    
    @app.route('/')
    @log_request
    def index():
        return "OK"
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert mock_log.called
        log_msg = mock_log.call_args[0][0]
        assert "GET / - " in log_msg
        assert "200 - " in log_msg

#Get back on it
"""
@patch('logging.Logger.error')
def test_log_request_error(mock_log):
    #Testuje logowanie requestu z błędem
    app = Flask(__name__)
    
    @app.route('/')
    @log_request
    def index():
        raise ValueError("Test error")
    
    with app.test_client() as client:
        with pytest.raises(ValueError):
            client.get('/')
        assert mock_log.called
        log_msg = mock_log.call_args[0][0]
        assert "GET / - " in log_msg
        assert "ERROR - " in log_msg
        assert "Test error" in log_msg
"""
# Testy dla handle_errors
def test_handle_errors_value_error():
    """Testuje przechwytywanie ValueError"""
    app = Flask(__name__)
    
    @app.route('/')
    @handle_errors
    def index():
        raise ValueError("Test error")
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 400
        assert b'Test error' in response.data

def test_handle_errors_file_not_found():
    """Testuje przechwytywanie FileNotFoundError"""
    app = Flask(__name__)
    
    @app.route('/')
    @handle_errors
    def index():
        raise FileNotFoundError("File not found")
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 404
        assert b'File not found' in response.data

def test_handle_errors_permission_error():
    """Testuje przechwytywanie PermissionError"""
    app = Flask(__name__)
    
    @app.route('/')
    @handle_errors
    def index():
        raise PermissionError("No access")
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 403
        assert b'Permission denied' in response.data

def test_handle_errors_unexpected_error():
    """Testuje przechwytywanie nieoczekiwanego błędu"""
    app = Flask(__name__)
    
    @app.route('/')
    @handle_errors
    def index():
        raise Exception("Unexpected error")
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 500
        assert b'Internal server error' in response.data

def test_handle_errors_no_error():
    """Testuje normalne działanie bez błędów"""
    app = Flask(__name__)
    
    @app.route('/')
    @handle_errors
    def index():
        return "OK"
    
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert b'OK' in response.data