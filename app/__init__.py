from flask import Flask, jsonify
from flask_cors import CORS
from .services.process_event import process_event_bp
import logging


def create_app():
    print("Creating the app...")
    app = Flask(__name__)
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Отключаем детальные логи для конкретных модулей
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Настройка CORS
    CORS(app)
    
    # Обработчик ошибок
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404
        
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
    # Регистрация blueprint
    app.register_blueprint(process_event_bp, url_prefix='/api/v1/')
    logger.info("Blueprint registered successfully")
    
    return app