from babel.dates import format_datetime as babel_format_datetime
from datetime import datetime
import pretty


def format_datetime(value, format='medium'):
    if format == 'full':
        format = "EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format = "EE dd.MM.y HH:mm"
    elif format == 'pretty':
        now = datetime.now()
        delta = now - value
        return pretty.date(now - delta)
    return babel_format_datetime(value, format)


def register_filters(jinja_env):
    jinja_env.filters['datetime'] = format_datetime
