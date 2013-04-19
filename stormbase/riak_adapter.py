from riak_async import RiakAsyncClient
from tornado import gen
from util import dump_json, load_json
from asyncouch.document import ViewResult
from uuid import uuid4


class RiakAdapter(RiakAsyncClient):
    @gen.engine
    def get(self, model, key, r=None, pr=None,
            vtag=None, callback=None):
        bucket_name = model.__name__
        (code, docs), _ = yield gen.Task(super(RiakAdapter, self).get,
                                         bucket_name, str(key), r, pr, vtag)
        if docs and model:
            docs = map(lambda x: model(load_json(x[1]), x[0]), docs)
            callback(ViewResult(docs))
        else:
            callback(docs)

    @gen.engine
    def put(self, value, key=None, metadata=None, vclock=None, w=None,
            dw=None, pw=None, return_body=True,
            if_none_match=False, callback=None):
        key = value.get('_id', key)
        if key is None:
            key = unicode(uuid4())
        bucket_name = value.__class__.__name__
        value = value._data_
        resp = yield gen.Task(super(RiakAdapter, self).put,
                              bucket_name, str(key), value, metadata,
                              vclock, w, dw, pw, return_body,
                              if_none_match)
        callback(resp)

    @gen.engine
    def put_new(self, robj, w=None, dw=None, pw=None, return_body=True,
                if_none_match=False, callback=None):
        robj = robj._data_
        bucket_name = robj.__class__.__name__
        resp = yield gen.Task(super(RiakAdapter, self).put_new,
                              bucket_name, robj, w, dw, pw, return_body,
                              if_none_match)
        callback(resp)
