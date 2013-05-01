from tuct import tuct
import json
#import jsonpickle
from datetime import datetime
#http://stackoverflow.com/questions/3768895/python-how-to-make-a-class-json-serializable

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


#class DateTimeHandler(jsonpickle.handlers.BaseHandler):
#    def flatten(obj, data):
#        return str(data)

#jsonpickle.handlers.registry.register(datetime, DateTimeHandler)


def dump_json(obj):
    return JSONEncoder().encode(obj)
    #return jsonpickle.encode(obj)


def load_json(string):
    return json.loads(string)
    #return jsonpickle.decode(string)
