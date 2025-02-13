from flask import Blueprint

bp = Blueprint('api', __name__)

# Import routes after creating blueprint to avoid circular imports
from . import dashboard, words, groups, study_activities, study_sessions, system