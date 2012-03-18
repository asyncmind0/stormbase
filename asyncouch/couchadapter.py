import os,re, codecs
import couch
import logging
from datetime import datetime
import json
import dateutil.parser
from uuid import uuid4
from debug import debug, trace
from tornado import gen

from stormbase.util import JSONEncoder

class ViewResult(list):
    offset = 0

class Document(dict):
    default = {}
    """Makes a dictionary behave like an object."""
    def __getattr__(self, name):
        if name == 'doc_type':
            return  self.__class__.__name__
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __init__(self,value={}):
        try :
            default = self.default
            type_keys = default.keys()
            val_keys = value.keys()
            for tkey in type_keys:
                if tkey in val_keys and value[tkey]:
                    if isinstance(default[tkey], datetime ):
                        if not isinstance(value[tkey], datetime) :
                            value[tkey] = dateutil.parser.parse(value[tkey])
                    else :
                        value[tkey] = type(default[tkey])(value[tkey])
                else :
                    value[tkey] = default[tkey]
            super(Document, self).__init__(value)
        except Exception as e:
            trace()

    @classmethod
    def add_defaults(cls,**kwargs):
        d = dict(**cls.default)
        d.update(**kwargs)
        return d


def wrap_results(data, model=Document):
    try:
        if not data:
            return []
        elif isinstance(data, Exception):
            raise data
        elif isinstance(data, list):
            data = filter( lambda x: x, data)
            values = ViewResult([ model(r) for r in data ])
            return values
        elif 'rows' in data.keys():
            rows = data['rows']
            values = ViewResult([ model(r['value']) for r in rows ])
            values.offset = data['offset']
            return values
        elif isinstance(data, dict):
            return model(data)
        else :
            raise Exception("Wierd results")
    except Exception as e:
        trace()
        raise e

def wrap_callback(cb, model=Document):
    def mycb(data):
        results = wrap_results(data, model)
        cb(results)
    return mycb

class CouchDbAdapter(couch.AsyncCouch):
    def __init__(self, db_name, create=True, callback=None, host='localhost', 
            resource_path=None, port=5984, ioloop=None, username=None,password=None):
        super(CouchDbAdapter,self).__init__( db_name, host=host, port=port, 
                username=username, password=password, ioloop=ioloop)
        self.initialize(callback, create, resource_path)

    @gen.engine
    def initialize(self, callback, create = True, resource_path=''):
        info = yield gen.Task(self.info_db)
        if hasattr(info,'code') and info.code == 404 :
            if not create:
                raise info
            res = yield gen.Task(self.create_db)
            info = yield gen.Task(self.info_db)
            info.update(res)
        if resource_path:
            yield gen.Task(self.init_resources,resource_path)
        callback(self, info)

    @gen.engine
    def init_resources(self, resource_path,callback):
        """ loads views into db
        TODO: remove deleted views
        """
        _design = os.path.join(resource_path,'_design')
        resources = {}
        def cb(arg,dirname, fname):
            if fname[0] in ['map.js','reduce.js']:
                key = '_design'+'/'+dirname.rsplit(os.path.sep,3)[1]
                viewname = dirname.rsplit(os.path.sep,3)[3]
                views = resources.get(key,[])
                views.append((viewname, os.path.join(dirname,fname[0])))
                resources[key] = views
        os.path.walk(_design, cb,None)
        docs = []

        for key in resources.keys():
            url = ''.join(['/', self.db_name, '/', key])
            doc = yield gen.Task(self._http_get,url)
            doc = doc if isinstance(doc,dict) else {'_id':key}
            for k,v in  resources[key]:
                if v.endswith('map.js'):
                    vtype = 'map'
                elif v.endswith('reduce.js'):
                    vtype = 'reduce'
                views = doc.get('views',{})
                views[k] = { vtype: read(v)}
                doc['views'] = views
            docs.append(doc)
        yield gen.Task(self.save_docs, docs)

        callback()

    def view(self, design_doc_name, view_name, callback=None, model=Document,**kwargs):
        super(CouchDbAdapter,self).view(design_doc_name,view_name, wrap_callback(callback, model), **kwargs)

    def get_doc(self, doc_id, model=Document, callback=None):
        super(CouchDbAdapter,self).get_doc(doc_id, wrap_callback(callback, model))

    def get_docs(self, doc_ids, model=Document, callback=None):
        super(CouchDbAdapter,self).get_docs(doc_ids, wrap_callback(callback, model))

    def save_doc(self, doc, callback=None):
        if '_id' not in doc:
            doc['_id'] = unicode(uuid4())
        doc['doc_type'] = doc.__class__.__name__
        super(CouchDbAdapter,self).save_doc(doc, callback)

    def _json_encode(self,value):
        return json.dumps(value, cls = JSONEncoder)


def read(fname, utf8=True, force_read=False):
    """ read file content"""
    if utf8:
        try:
            with codecs.open(fname, 'rb', "utf-8") as f:
                return f.read()
        except UnicodeError, e:
            if force_read:
                return read(fname, utf8=False)
            raise
    else:
        with open(fname, 'rb') as f:
            return f.read()

