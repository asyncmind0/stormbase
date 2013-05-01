import corduroy
from corduroy.atoms import View, odict
from corduroy.config import defaults
import jsonpickle
import json as _json
from uuid import uuid4
from tornado import gen


class JSONEncoder(_json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        return super(JSONEncoder, self).default(obj)

class json(object):    
    @classmethod
    def decode(cls, string, **opts):
        """Decode the given JSON string.

        :param string: the JSON string to decode
        :type string: basestring
        :return: the corresponding Python data structure
        :rtype: object
        """
        return _json.loads(string, 
                           object_hook=defaults.types.dict, **opts)
        #return jsonpickle.decode(string)

    @classmethod
    def encode(cls, obj, **opts):
        """Encode the given object as a JSON string.

        :param obj: the Python data structure to encode
        :type obj: object
        :return: the corresponding JSON string
        :rtype: basestring
        """
        return _json.dumps(obj, allow_nan=False, cls=JSONEncoder,
                           ensure_ascii=False, encoding='utf-8', **opts)
        #return jsonpickle.encode(obj)

corduroy.config.json = json
corduroy.couchdb.json = json
corduroy.io.json = json

class CouchDBAdapter(object):
    def __init__(self, db):
        self.db = db

    def _handle_results(self, result, model):
        result = result[0][0]
        if result and isinstance(result, list):
            if len(result) > 1:
                result = [model(x) for x in result]
            else:
                result = model(result.rows.pop())
        elif result:
            result = model(result)
          
        return result

    @gen.engine
    def get(self, key, model, callback=None, **kwarg):
        result = yield gen.Task(self.db.get, key, **kwarg)
        callback(self._handle_results(result, model))

    @gen.engine
    def save(self, docs, callback=None, **kwargs):
        if not isinstance(docs, list):
            docs = [docs]
        for doc in docs:
            if not doc.get('_id'):
                doc['_id'] = unicode(uuid4())
        doc['doc_type'] = doc.__class__.__name__
        result = yield gen.Task(self.db.save, doc)
        callback(result)

    @gen.engine
    def view(self, view, model=None, callback=None, **kwargs):
        if model:
            view  = "%s/%s" % (model.__name__.lower(), view)
        result = yield gen.Task(
            self.db.view, view, **kwargs)
        result = result[0][0]
        #if kwargs.get('reduce'):
        if result and kwargs.get('include_docs', True):
            result.rows = [model(x.value) if isinstance(x.value, dict) and model
                           else x.value for x in result.rows]
        callback(result)

    @gen.engine
    def delete(self, key, callback=None, **kwarg):
        result = yield gen.Task(self.db.delete, key, **kwarg)
        callback(result)
