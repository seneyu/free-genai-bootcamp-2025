from flask import Flask, jsonify
from app.extensions import db, migrate
from app.commands.cli import init_cli
from app.errors import error_response
from config import config

from app.models.word import Word
from app.models.group import Group
from app.models.study_activity import StudyActivity

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # initialize CLI commands
    init_cli(app)

    # register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return error_response(404)

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return error_response(500)
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return error_response(400)

    # ensure all responses are JSON
    @app.after_request
    def ensure_json_response(response):
        response.headers['Content-Type'] = 'application/json'
        return response

    # register blueprint
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def hello():
        return jsonify({'message': 'Hello, Lang Portal!'})

    return app