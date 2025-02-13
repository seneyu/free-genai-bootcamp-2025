import pytest
from app import create_app
from app.extensions import db
from tests.test_helpers import create_test_data

@pytest.fixture
def app():
    """create and configure a test Flask application instance"""
    app = create_app('testing')
    
    # create tables for test database
    with app.app_context():
        db.create_all()
        create_test_data(app)
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """create a test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """create a test CLI runner"""
    return app.test_cli_runner() 