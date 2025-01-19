from flask import Flask
from .services.process_event import process_event_bp


def create_app():
    print("Creating the app...")
    app = Flask(__name__)
    print("App created successfully")
    #register blueprints
    app.register_blueprint(process_event_bp, url_prefix='/api/v1/')
    print("Blueprint registered successfully")
    return app