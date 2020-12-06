from typing import Union, Dict
from flask import Flask, request


app = Flask(__name__)

with app.app_context():
    from modules import actors
    app.register_blueprint(actors.bp)


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
