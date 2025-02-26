from flask import jsonify
import traceback
import logging

# Set up error logging
logger = logging.getLogger('api_errors')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler('api_errors.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def register_error_handlers(app):
    @app.errorhandler(500)
    def handle_500_error(e):
        # Log the error with traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Internal Server Error:\n{error_traceback}")
        
        return jsonify({
            "error": "Internal Server Error",
            "message": "The server encountered an unexpected condition which prevented it from fulfilling the request."
        }), 500
    
    @app.errorhandler(404)
    def handle_404_error(e):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found on the server."
        }), 404
    
    @app.errorhandler(400)
    def handle_400_error(e):
        return jsonify({
            "error": "Bad Request",
            "message": "The server could not understand the request due to invalid syntax."
        }), 400

def setup_api_logging(app):
    # Log all requests in development mode
    if app.debug:
        @app.before_request
        def log_request_info():
            from flask import request
            app.logger.debug('Headers: %s', request.headers)
            app.logger.debug('Body: %s', request.get_data())