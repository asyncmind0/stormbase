import json
import jsonpickle
from datetime import datetime


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

class DateTimeHandler(jsonpickle.handlers.BaseHandler):
    def flatten(obj, data):
        return str(data)

jsonpickle.handlers.registry.register(datetime, DateTimeHandler)

def dump_json(obj):
    return jsonpickle.encode(obj)
