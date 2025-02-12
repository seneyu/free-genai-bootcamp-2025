import click
from flask.cli import with_appcontext
from app.database.seeds import Seeder 

def init_cli(app):
    @app.cli.group()
    def seed():
        """seed database commands"""
        pass

    @seed.command()
    @with_appcontext
    def run():
        """run database seeds"""
        click.echo('Seeding database...')
        Seeder.seed_all()
        click.echo('Database seeded successfully!')