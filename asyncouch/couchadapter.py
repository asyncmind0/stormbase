from debug import shell, debug as sj_debug
import os
import re
import codecs
import couch
import logging
from datetime import datetime
import json
import dateutil.parser
from uuid import uuid4
from debug import debug, trace
from tornado import gen
from collections import MutableMapping

from util import JSONEncoder


class ViewResult(list):
    offset = 0


class Document(MutableMapping):
    _data_ = {}

    def __len__(self):
        return self._data_.__len__()

    def __iter__(self):
        return self._data_.__iter__()

    def __getitem__(self, name):
        return self._data_[name]
    
    def __setitem__(self, name, value):
        self._data_[name] = value
        
    def __delitem__(self, name):
        del self._data_[name]

    def __getattr__(self, name):
        if name == 'doc_type':
            return self.__class__.__name__
        if name == '_data_' or name.startswith("__"):
            return object.__getattr__(self, name)
        values_dict = self._data_
        if name in values_dict:
            return values_dict[name]
        else:
            return object.__getattr__(self, name)

    def __setattr__(self, name, value):
        if name == '_data_' or name.startswith("__"):
            super(Document, self).__setattr__(name, value)
        else:
            self._data_[name] = value

    @classmethod
    def get_defaults(self):
        raise NotImplementedError()

    def __init__(self, value=None):
        #self._values_dict.update(default)
        default = self.__class__.defaults
        #print value
        type_keys = default.keys()
        if value is None:
            value = {}
        val_keys = value.keys()
        for tkey in type_keys:
            if tkey in val_keys and value[tkey]:
                if isinstance(default[tkey], datetime):
                    if not isinstance(value[tkey], datetime):
                        value[tkey] = dateutil.parser.parse(value[tkey])
                else:
                    value[tkey] = type(default[tkey])(value[tkey])
            else:
                value[tkey] = default[tkey]
        
        #for key in default:
        #    if key not in value:
        #        value[key] = default[key]
        self._data_ = value



def wrap_results(data, model=Document):
    if not data:
        return None
    elif isinstance(data, couch.NotFound):
        return None
    elif isinstance(data, Exception):
        raise data
    elif isinstance(data, list):
        data = filter(lambda x: x, data)
        values = ViewResult([model(r) for r in data])
        return values
    elif 'rows' in data.keys():
        rows = data['rows']
        values = map(lambda x: x['value'], rows)
        if values and isinstance(values[0], dict):
            values = ViewResult(map(model, values))
            values.offset = data.get('offset', 0)
            data['rows'] = values
        return data
    elif isinstance(data, dict):
        return model(data)
    else:
        raise Exception("Wierd results")


def wrap_callback(cb, model=Document):
    def mycb(data):
        results = wrap_results(data, model)
        cb(results)
    return mycb


class CouchDbAdapter(couch.AsyncCouch):
    def __init__(self, db_name, create=True, callback=None, host='localhost',
                 resource_path=None, port=5984, ioloop=None, username=None,
                 password=None):
        super(CouchDbAdapter, self).__init__(
            db_name, host=host, port=port, username=username,
            password=password, ioloop=ioloop)
        self.initialize(callback, create, resource_path)

    @gen.engine
    def initialize(self, callback, create=True, resource_path=''):
        info = yield gen.Task(self.info_db)
        if hasattr(info, 'code') and info.code == 404:
            if not create:
                raise info
            res = yield gen.Task(self.create_db)
            if isinstance(res, Exception):
                raise res
            info = yield gen.Task(self.info_db)
            info.update(res)
        if resource_path:
            yield gen.Task(self.init_resources, resource_path)
        callback(db=self, info=info)

    def init_resources(self, resource_path, callback):
        """ loads views into db
        TODO: remove deleted views
        """
        _design = os.path.join(resource_path, '_design')
        models = []
        try:

            def cb(arg, dirname, fname):
                if fname[0] in ['map.js', 'reduce.js']:
                    models.append(dirname.rsplit(os.path.sep, 3)[1])
            os.path.walk(_design, cb, None)
            couchapp_cmd = "couchapp push {0}/{1} {2}/{3}".format(
                _design, "%s", self.couch_url, self.db_name)
            map(lambda x: os.system(couchapp_cmd % x), set(models))
        except Exception as e:
            logging.error("Failed to init_resources. %s", e)

        callback()

    def view(self, design_doc_name, view_name, callback=None,
             model=Document, **kwargs):
        super(CouchDbAdapter, self).view(
            design_doc_name, view_name, wrap_callback(callback, model),
            **kwargs)

    def get_doc(self, doc_id, model=Document, callback=None):
        super(CouchDbAdapter, self).get_doc(doc_id, wrap_callback(
            callback, model))

    def get_docs(self, doc_ids, model=Document, callback=None):
        super(CouchDbAdapter, self).get_docs(doc_ids,
                                             wrap_callback(callback, model))

    def save_doc(self, doc, callback=None):
        if not doc.get('_id'):
            doc['_id'] = unicode(uuid4())
        doc['doc_type'] = doc.__class__.__name__
        def save_callback(savedoc):
            if isinstance(savedoc, dict) and savedoc.get('ok'):
                doc['_rev'] = savedoc['rev']
            return callback(savedoc)
            
        super(CouchDbAdapter, self).save_doc(doc._data_, save_callback)

    def _json_encode(self, value):
        return json.dumps(value, cls=JSONEncoder)


def read(fname, utf8=True, force_read=False):
    """ read file content"""
    if utf8:
        try:
            with codecs.open(fname, 'rb', "utf-8") as f:
                return f.read()
        except UnicodeError:
            if force_read:
                return read(fname, utf8=False)
            raise
    else:
        with open(fname, 'rb') as f:
            return f.read()
