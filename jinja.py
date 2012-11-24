from babel.dates import format_datetime as babel_format_datetime


def format_datetime(value, format='medium'):
    if format == 'full':
        format = "EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format = "EE dd.MM.y HH:mm"
    return babel_format_datetime(value, format)


def register_filters(jinja_env):
    jinja_env.filters['datetime'] = format_datetime
