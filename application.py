import os
from typing import Dict, Union

from flask import Flask, render_template, request
from flask_sqlalchemy import BaseQuery, SQLAlchemy

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
        def inner_wrapper(*args, **kwargs):
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

        return inner_wrapper

    return wrapper


@app.route('/actors/', methods=['GET'])
@paginate_list({
    'actor_id': Actor.actor_id,
    'first_name': Actor.first_name,
    'last_name': Actor.last_name,
    'last_update': Actor.last_update,
}, {
    'actor_id': 'ID',
    'first_name': 'First name',
    'last_name': 'Last name',
    'last_update': 'Last update',
})
def actors() -> BaseQuery:
    return Actor.query
