import datetime
import zipfile
from typing import Dict, Tuple

from flask import render_template, request, Response, stream_with_context
from flask_sqlalchemy import BaseQuery
from xlsx_streaming.render import _get_column_letter
from xlsx_streaming.streaming import zip_to_zipstream
from xlsx_streaming.xlsx_template import DEFAULT_TEMPLATE

from db import get_db

DB = get_db()


class AbstractModel(DB.Model):
    __abstract__ = True

    def to_csv_row(self) -> str:
        raise NotImplementedError()

    def to_xlsx_row(self) -> Tuple[str]:
        raise NotImplementedError()

    @staticmethod
    def titles() -> Dict[str, str]:
        raise NotImplementedError()


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


def generate_csv(model: AbstractModel):
    model_gen = model.query.yield_per(100)
    headers = model.titles().values()
    yield f"{','.join(headers)}\n"
    yield from map(model.to_csv_row, model_gen)


def generate_xlsx(model: AbstractModel):
    def render_row(values, line_number):
        cells = (
            f'<c r="{_get_column_letter(position)}{line_number}" t="inlineStr"><is><t>{value}</t></is></c>'
            for position, value in enumerate(values, start=1)
        )

        return f"""<row r="{line_number}">{''.join(cells)}</row>""".encode('utf-8')

    def render_worksheet(data):
        yield (
            b'<worksheet'
            b' xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            b' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<sheetViews><sheetView>'
            b'<pane xSplit="0" ySplit="1" topLeftCell="A2" state="frozen"/>'
            b'</sheetView></sheetViews>'
            b'<sheetData>'
        )
        headers = model.titles().values()
        yield render_row(headers, 1)
        yield from (
            render_row(row.to_xlsx_row(), row_number)
            for row_number, row in enumerate(data, start=2)
        )

        yield b'</sheetData></worksheet>'

    zip_template = zipfile.ZipFile(DEFAULT_TEMPLATE, mode='r')
    sheet_name = 'xl/worksheets/sheet1.xml'
    zipped_stream = zip_to_zipstream(zip_template, exclude=[sheet_name])

    worksheet_stream = render_worksheet(model.query.yield_per(100))
    zipped_stream.write_iter(
        arcname=sheet_name,
        iterable=worksheet_stream,
        compress_type=zipfile.ZIP_DEFLATED,
    )

    return zipped_stream


def export_data(model: AbstractModel, file_extension: str):
    generator = generate_xlsx if file_extension == 'xlsx' else generate_csv
    file_name = f'{model.__tablename__}_list_{datetime.datetime.now()}.{file_extension}'
    headers = {
        'Content-Disposition': f"attachment;filename={file_name}"
    }
    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_extension == 'xlsx' else 'text/csv'

    return Response(
        stream_with_context(generator(model)),
        mimetype=mimetype,
        headers=headers,
    )
