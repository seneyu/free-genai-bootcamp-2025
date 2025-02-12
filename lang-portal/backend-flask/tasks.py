# tasks.py
from invoke import task

@task
def init_db(ctx):
    """Initialize the database and migrations"""
    ctx.run("flask db init")
    ctx.run("flask db migrate -m 'Initial migration'")
    ctx.run("flask db upgrade")

@task
def make_migration(ctx, message):
    """Create a new migration"""
    ctx.run(f"flask db migrate -m '{message}'")

@task
def apply_migration(ctx):
    """Apply pending migrations"""
    ctx.run("flask db upgrade")

@task
def rollback_migration(ctx):
    """Rollback the last migration"""
    ctx.run("flask db downgrade")

@task
def seed_db(ctx):
    """Seed the database with initial data"""
    ctx.run("flask seed run")

@task
def run_dev(ctx):
    """Run the development server"""
    ctx.run("flask run --debug")

@task
def test(ctx):
    """Run tests"""
    ctx.run("pytest tests/")

@task
def clean(ctx):
    """Remove Python file artifacts"""
    ctx.run("find . -name '*.pyc' -delete")
    ctx.run("find . -name '*.pyo' -delete")
    ctx.run("find . -name '__pycache__' -delete")

@task
def lint(ctx):
    """Run linter"""
    ctx.run("flake8 app/ tests/")