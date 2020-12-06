import os

from flask import current_app, g
from flask_sqlalchemy import SQLAlchemy


def get_db():
    if 'db' not in g:
        current_app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_CONN')
        current_app.config['SQLALCHEMY_ECHO'] = True
        g.db = SQLAlchemy(current_app, session_options={'autocommit': True})
    return g.db
