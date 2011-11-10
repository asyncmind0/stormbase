import couch
import logging
from datetime import datetime
import json
import dateutil.parser
from uuid import uuid4
from stormbase.debug import debug, trace


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

class CouchEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

class CouchDbAdapter(couch.AsyncCouch):
    def __init__(self, db_name, on_ready, host='localhost', port=5984):
        super(CouchDbAdapter,self).__init__( db_name, host, port)
        def on_info(info):
            if hasattr(info,'code') and info.code == 404 :
                self.create_db(lambda info: on_ready(self,info))
            else :
                on_ready(self, info)
        self.info_db(on_info)

    def view(self, design_doc_name, view_name, callback=None, model=Document,**kwargs):
        super(CouchDbAdapter,self).view(design_doc_name,view_name, _w(callback, model), **kwargs)

    def get_doc(self, doc_id, model=Document, callback=None):
        super(CouchDbAdapter,self).get_doc(doc_id, _w(callback, model))

    def get_docs(self, doc_ids, model=Document, callback=None):
        super(CouchDbAdapter,self).get_docs(doc_ids, _w(callback, model))

    def save_doc(self, doc, callback=None):
        if '_id' not in doc:
            doc['_id'] = unicode(uuid4())
        if isinstance(doc, Document):
            doc['doc_type'] = doc.__class__.__name__
        super(CouchDbAdapter,self).save_doc(doc, callback)

    def _json_encode(self,value):
        return json.dumps(value, cls = CouchEncoder)

def wrap_results(data, model=Document):
    try:
        if isinstance(data, couch.NotFound) or not data:
            return []
        elif isinstance(data, couch.CouchException):
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
        else :
            return model(data)
    except Exception as e:
        trace()
        sj_debug() ############################## Breakpoint ##############################

def _w(cb, model=Document):
    def mycb(data):
        results = wrap_results(data, model)
        cb(results)
    return mycb
