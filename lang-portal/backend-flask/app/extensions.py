from flask import abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def get_or_404(model, id):
    """helper function to get a model by id or return 404"""
    instance = db.session.get(model, id)
    if instance is None:
        abort(404)
    return instance