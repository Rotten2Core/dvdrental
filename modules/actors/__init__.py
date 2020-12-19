from flask import Blueprint, redirect, render_template, request
from flask_sqlalchemy import BaseQuery

from common import paginate_list, render_item, AbstractModel, export_data
from db import get_db

bp = Blueprint('actors', __name__, url_prefix='/actors')
db = get_db()


class Actor(AbstractModel):
    actor_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45), nullable=False)
    last_name = db.Column(db.String(45), nullable=False)
    last_update = db.Column(db.DateTime(timezone=False), nullable=False)

    def to_csv_row(self):
        return f"""{','.join((
            str(self.actor_id),
            self.first_name,
            self.last_name,
            self.last_update.strftime('%d.%m.%Y %H:%M:%S'),
        ))}\n"""

    def to_xlsx_row(self):
        return (
            str(self.actor_id),
            self.first_name,
            self.last_name,
            self.last_update.strftime('%d.%m.%Y %H:%M:%S'),
        )

    @staticmethod
    def titles():
        return {
            'actor_id': 'ID',
            'first_name': 'First name',
            'last_name': 'Last name',
            'last_update': 'Last update',
        }


@bp.route('/', methods=['GET'])
@paginate_list(
    {
        'actor_id': Actor.actor_id,
        'first_name': Actor.first_name,
        'last_name': Actor.last_name,
        'last_update': Actor.last_update,
    },
    Actor.titles(),
)
def actors() -> BaseQuery:
    return Actor.query


@bp.route('/<int:actor_id>/', methods=['GET'])
@render_item(Actor.titles())
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
            titles=Actor.titles(),
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


@bp.route('/export/<file_extension>/', methods=['GET'])
def actors_export(file_extension):
    return export_data(Actor, file_extension)
