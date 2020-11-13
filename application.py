import os

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_CONN')
db = SQLAlchemy(app)


class Actor(db.Model):
    actor_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45), nullable=False)
    last_name = db.Column(db.String(45), nullable=False)
    last_update = db.Column(db.DateTime(timezone=False), nullable=False)


@app.context_processor
def utility_processor():
    def format_value(value) -> str:
        if isinstance(value, (int, str)):
            return value

        return value.strftime('%d.%m.%Y %H:%M:%S')

    def format_get_params(**kwargs) -> str:
        params = []
        request_args = dict(request.args)
        request_args.update(kwargs)
        for key, value in request_args.items():
            params.append('{}={}'.format(key, value))

        return '?{}'.format('&'.join(params))

    return dict(format_value=format_value, format_get_params=format_get_params)


@app.route('/actors/')
def actor():
    sort_keys = {
        'id': Actor.actor_id,
        'first_name': Actor.first_name,
        'last_name': Actor.last_name,
        'last_update': Actor.last_update,
    }
    sort = request.args.get('sort', 'id')
    page = int(request.args.get('page', 1))
    if page <= 0:
        page = 1

    page_size = int(request.args.get('page_size', 25))
    offset = page_size * (page - 1)
    actors = Actor.query.order_by(sort_keys.get(sort, sort_keys['id'])).limit(25).offset(offset).all()

    return render_template('list.html', title='Actors', data=actors, page=page, sort=sort)
