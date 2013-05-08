import corduroy
from corduroy.atoms import View, odict
from corduroy.config import defaults
import jsonpickle
import json as _json
from uuid import uuid4
import tornado
from tornado import gen
from datetime import datetime
from tornado.concurrent import Future
from tornado import httputil, stack_context


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

    def _handle_results(self, future, result, model):
        result = result[0]
        if result and isinstance(result, list):
            if len(result) > 1:
                result = [model(x) for x in result]
            else:
                result = model(result.rows.pop())
        elif result:
            result = model(result)
        future.set_result(result)
        return result

    def get(self, key, model, callback=None, **kwarg):
        future = Future()
        if callback is not None:
            callback = stack_context.wrap(callback)
            def handle_future(future):
                exc = future.exception()
                if exc is not None:
                    logging.exception(exc)
                response = future.result()
                ioloop = tornado.ioloop.IOLoop.instance()
                ioloop.add_callback(callback, response)
            future.add_done_callback(handle_future)
        result = self.db.get(
            key, callback=lambda data, status: self._handle_results(future, (data, status), model),
            **kwarg)
        return future

    def save(self, docs, callback=None, **kwargs):
        if not isinstance(docs, list):
            docs = [docs]
        for doc in docs:
            if not doc.get('_id'):
                doc['_id'] = unicode(uuid4())
        doc['doc_type'] = doc.__class__.__name__
        future = Future()
        if callback is not None:
            callback = stack_context.wrap(callback)
            def handle_future(future):
                exc = future.exception()
                if exc is not None:
                    logging.exception(exc)
                response = future.result()
                ioloop = tornado.ioloop.IOLoop.instance()
                ioloop.add_callback(callback, *response)
            future.add_done_callback(handle_future)
        def handle_result(data, status):
            future.set_result((data, status))
        result = self.db.save(
            doc, callback=handle_result)

        return future

    def view(self, view, model=None, callback=None, **kwargs):
        future = Future()
        if model:
            view  = "%s/%s" % (model.__name__.lower(), view)
        if callback is not None:
            callback = stack_context.wrap(callback)

            def handle_future(future):
                exc = future.exception()
                #if isinstance(exc, HTTPError) and exc.response is not None:
                #    response = exc.response
                #elif exc is not None:
                #    response = HTTPResponse(
                #        request, 599, error=exc,
                #        request_time=time.time() - request.start_time)
                #else:
                response = future.result()
                ioloop = tornado.ioloop.IOLoop.instance()
                ioloop.add_callback(callback, response)
            future.add_done_callback(handle_future)
        def handle_result(result, status):
            if result and kwargs.get('include_docs', True):
                result.rows = [model(x.value) if isinstance(x.value, dict) and model
                               else x.value for x in result.rows]
            future.set_result(result)
        self.db.view(view, callback=handle_result, **kwargs)
        return future

    def delete(self, key, callback=None, **kwarg):
        future = Future()
        if callback is not None:
            callback = stack_context.wrap(callback)
            def handle_future(future):
                exc = future.exception()
                if exc is not None:
                    logging.exception(exc)
                response = future.result()
                ioloop = tornado.ioloop.IOLoop.instance()
                ioloop.add_callback(callback, response)
            future.add_done_callback(handle_future)
        result = self.db.delete(key,
                                callback=lambda r: future.set_result(r),
                                **kwarg)
        return future
