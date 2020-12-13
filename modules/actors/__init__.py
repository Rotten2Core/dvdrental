import datetime
import zipfile

from flask import Blueprint, redirect, render_template, request, Response, stream_with_context
from flask_sqlalchemy import BaseQuery
from xlsx_streaming.render import _get_column_letter
from xlsx_streaming.streaming import zip_to_zipstream

from xlsx_streaming.xlsx_template import DEFAULT_TEMPLATE

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


@bp.route('/export/<file_extension>/', methods=['GET'])
def actors_export(file_extension):
    file_name = f'actors_list_{datetime.datetime.now()}.{file_extension}'
    headers = {
        'Content-Disposition': f"attachment;filename={file_name}"
    }
    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_extension == 'xlsx' else 'text/csv'

    def generate_csv():
        actors_gen = Actor.query.yield_per(100)
        yield from map(Actor.to_csv_row, actors_gen)

    def generate_xlsx():
        def render_worksheet(data):
            yield (
                b'<worksheet'
                b' xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
                b' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                b'<sheetData>'
            )

            yield from (
                render_row(row.to_xlsx_row(), row_number).encode('utf-8')
                for row_number, row in enumerate(data, start=1)
            )

            yield b'</sheetData></worksheet>'

        def render_row(values, line_number):
            cells = (
                f'<c r="{_get_column_letter(position)}{line_number}" t="inlineStr"><is><t>{value}</t></is></c>'
                for position, value in enumerate(values, start=1)
            )

            return f"""<row r="{line_number}">{''.join(cells)}</row>"""

        zip_template = zipfile.ZipFile(DEFAULT_TEMPLATE, mode='r')
        sheet_name = 'xl/worksheets/sheet1.xml'
        zipped_stream = zip_to_zipstream(zip_template, exclude=[sheet_name])

        worksheet_stream = render_worksheet(Actor.query.yield_per(100))
        zipped_stream.write_iter(
            arcname=sheet_name,
            iterable=worksheet_stream,
            compress_type=zipfile.ZIP_DEFLATED,
        )

        return zipped_stream

    return Response(
        stream_with_context(generate_xlsx() if file_extension == 'xlsx' else generate_csv()),
        mimetype=mimetype,
        headers=headers,
    )
