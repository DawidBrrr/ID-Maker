from flask import Flask, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
import atexit
import threading
import time

from .config import config
from .routes import register_routes
from .services.image_service import image_service
from .services.task_service import task_service
from .utils.helpers import cleanup_filesystem

def create_app():
    """Factory function do tworzenia aplikacji Flask"""
    app = Flask(__name__)
    
    # Konfiguracja
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    #app.config['DEBUG'] = config.DEBUG
    
    # CORS - bardziej restrykcyjne w produkcji
    #if config.DEBUG:
    CORS(app)
    #else:
        #CORS(app, origins=['https://kadr-backend.onrender.com'])
    
    # Logging
    setup_logging(app)
    
    # Rejestracja routes
    register_routes(app)
    
    # Error handlers
    register_error_handlers(app)
    
    # Background tasks
    start_background_tasks()
    
    # Cleanup on exit
    atexit.register(cleanup_on_exit)
    
    app.logger.info("Application started successfully")
    
    return app

def setup_logging(app):
    """Konfiguruje logging"""
    if not app.debug:
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # File handler
        file_handler = RotatingFileHandler(
            'logs/app.log', 
            maxBytes=25 * 1024 * 1024,  # 25MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

def register_error_handlers(app):
    """Rejestruje error handlers"""
    
    @app.errorhandler(413)
    def too_large(e):
        app.logger.warning("File too large uploaded")
        return jsonify({'error': 'File too large', 'max_size': f'{config.MAX_CONTENT_LENGTH/1024/1024:.1f}MB'}), 413
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f'Server Error: {e}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f'Unhandled exception: {e}', exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

def cleanup_old_files():
    """Background task do czyszczenia starych plików"""
    while True:
        try:
            # Cleanup old tasks
            removed_tasks = task_service.cleanup_old_tasks()
            if removed_tasks > 0:
                logging.info(f"Cleaned up {removed_tasks} old tasks")
            
            # Cleanup old files from filesystem
            cleanup_filesystem(config.UPLOAD_FOLDER, config.MAX_FILE_AGE_HOURS)
            cleanup_filesystem(config.OUTPUT_FOLDER, config.MAX_FILE_AGE_HOURS)
            cleanup_filesystem(config.ERROR_FOLDER, config.MAX_FILE_AGE_HOURS)

            # Sleep for 1 hour
            time.sleep(3600)
            
        except Exception as e:
            logging.error(f"Error in cleanup task: {e}")
            time.sleep(300)  # Sleep 5 minutes on error

def start_background_tasks():
    """Startuje background tasks"""
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()

def cleanup_on_exit():
    """Cleanup na wyjściu z aplikacji"""
    try:
        image_service.shutdown()
        logging.info("Application shutdown completed")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")