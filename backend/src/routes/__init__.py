from flask import Blueprint

def register_routes(app):
    """Rejestruje wszystkie blueprinty"""
    from .upload import upload_bp
    from .status import status_bp
    from .files import files_bp
    from .health import health_bp
    
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(status_bp, url_prefix='/api')
    app.register_blueprint(files_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')