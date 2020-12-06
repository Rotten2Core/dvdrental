from flask import Blueprint, redirect, render_template, request

from flask_sqlalchemy import BaseQuery

from common import paginate_list, render_item
from db import get_db

bp = Blueprint('actors', __name__, url_prefix='/actors')
db = get_db()

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


@bp.route('/', methods=['GET'])
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


@bp.route('/<int:actor_id>/', methods=['GET'])
@render_item(TITLES)
def get_actor(actor_id):
    return Actor.query.get_or_404(actor_id)


@bp.route('/<int:actor_id>/edit/', methods=['GET', 'POST'])
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
