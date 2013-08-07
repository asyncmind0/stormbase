import corduroy
from corduroy.atoms import View, odict
from corduroy.config import defaults
import tornado
from tornado import gen
from tornado.concurrent import Future, return_future
from tornado import httputil, stack_context
import json as _json
from uuid import uuid4
from datetime import datetime

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

corduroy.config.json = json
corduroy.couchdb.json = json
corduroy.io.json = json

class CouchDBAdapter(object):
    """ Wraps a corduroy Database class and converts results into BaseDocument objects.
    """
    def __init__(self, db):
        self.db = db

    def _handle_results(self, future, result, model):
        result = result[0]
        if result and isinstance(result, list):
            result = [model(x) for x in result]
        elif result:
            result = model(result)
        future.set_result(result)

    def get(self, key, model, **kwarg):
        future = Future()
        result = self.db.get(
            key, callback=lambda data, status: self._handle_results(
                future, (data, status), model), **kwarg)
        return future

    def save(self, docs, **kwargs):
        if not isinstance(docs, list):
            docs = [docs]
        for doc in docs:
            if not doc.get('_id'):
                doc['_id'] = unicode(uuid4())
        doc['doc_type'] = doc.__class__.__name__
        future = Future()
        result = self.db.save(
            doc, callback=lambda data, status: future.set_result((data, status)))

        return future

    def view(self, view, model=None, **kwargs):
        future = Future()
        if model:
            view  = "%s/%s" % (model.__name__.lower(), view)
        def handle_result(result, status):
            if result and kwargs.get('include_docs', True):
                result.rows = [model(x.value) if isinstance(x.value, dict)
                               and model
                               else x.value for x in result.rows]
            future.set_result(result)
        self.db.view(view, callback=handle_result, **kwargs)
        return future

    def delete(self, key, callback=None, **kwarg):
        future = Future()
        result = self.db.delete(
            key, callback=lambda r: future.set_result(r), **kwarg)
        return future
