import datetime
from flask import Flask, render_template


app = Flask(__name__)


@app.context_processor
def utility_processor():
    def format_value(value) -> str:
        if isinstance(value, (int, str)):
            return value

        return value.strftime('%d.%m.%Y %H:%M:%S')

    return dict(format_value=format_value)


@app.route('/actor/')
def actor():
    actors = [{
        'id': 17,
        'first_name': 'Serhii',
        'last_name': 'Kozyr',
        'last_update': datetime.datetime.now(),
    }, {
        'id': 13,
        'first_name': 'Mykyta',
        'last_name': 'Velykanov',
        'last_update': datetime.datetime.now() - datetime.timedelta(minutes=30),
    }]

    return render_template('list.html', title='Actors', data=actors)
