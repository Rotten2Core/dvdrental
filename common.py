from flask import render_template, request
from flask_sqlalchemy import BaseQuery


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
