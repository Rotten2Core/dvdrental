import os
from typing import Dict, Union

from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import BaseQuery, SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_CONN')
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app, session_options={'autocommit': True})

TITLES = {
    'actor_id': 'ID',
    'first_name': 'First name',
    'last_name': 'Last name',
    'last_update': 'Last update',
}


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

    def format_get_params(_output='str', **kwargs) -> Union[str, Dict]:
        params = {}
        request_args = dict(request.args)
        request_args.update(kwargs)
        for key, value in request_args.items():
            params[key] = value

        if _output == 'dict':
            return params

        return '?{}'.format('&'.join(f'{key}={value}' for key, value in params.items()))

    return dict(format_value=format_value, format_get_params=format_get_params)


def paginate_list(sort_keys, header):
    def wrapper(func):
        def list_inner_wrapper(*args, **kwargs):
            sort = request.args.get('sort', 'actor_id')
            page = max(int(request.args.get('page', 1)), 1)
            per_page = min(int(request.args.get('per_page', 25)), 100)
            offset = per_page * (page - 1)

            query: BaseQuery = func(*args, **kwargs)
            data = query.order_by(
                sort_keys.get(sort, sort_keys['actor_id']),
            ).limit(
                per_page,
            ).offset(
                offset,
            ).all()
            count = query.count()

            return render_template(
                'list.html',
                header=header,
                sort_keys=sort_keys,
                data=data,
                count=count,
                page=page,
                per_page=per_page,
            )

        return list_inner_wrapper

    return wrapper


def render_item(titles):
    def wrapper(func):
        def item_inner_wrapper(*args, **kwargs):
            data = func(*args, **kwargs)

            return render_template(
                'item.html',
                data=data,
                titles=titles,
            )

        return item_inner_wrapper

    return wrapper


@app.route('/actors/', methods=['GET'])
@paginate_list(
    {
        'actor_id': Actor.actor_id,
        'first_name': Actor.first_name,
        'last_name': Actor.last_name,
        'last_update': Actor.last_update,
    },
    TITLES,
)
def actors() -> BaseQuery:
    return Actor.query


@app.route('/actors/<int:actor_id>/', methods=['GET'])
@render_item(TITLES)
def get_actor(actor_id):
    return Actor.query.get_or_404(actor_id)


@app.route('/actors/<int:actor_id>/edit/', methods=['GET', 'POST'])
def edit_actor(actor_id):
    edit_fields = ('first_name', 'last_name')

    if request.method == 'GET':
        return render_template(
            'item.html',
            data=Actor.query.get_or_404(actor_id),
            edit_fields=edit_fields,
            titles=TITLES,
        )

    if request.method == 'POST':
        values = {
            field: request.form[field]
            for field in edit_fields
            if field in request.form
        }
        if values:
            Actor.query.filter(Actor.actor_id == actor_id).update(values)

        return redirect(f'/actors/{actor_id}')
