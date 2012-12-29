import os
from datetime import datetime
from asyncouch import couchadapter
import unittest
from tornado.options import options
from asyncouch.couchadapter import Document
from tornado.testing import AsyncTestCase, LogTrapTestCase


class TestDocument(Document):
    """Base User objext
    """
    default = Document.add_defaults(
        string_attr="",
        list_attr=[],
        int_attr=0,
        date_attr=datetime.utcnow())


class CouchDbAdapterTest(AsyncTestCase, LogTrapTestCase):
    db_name = 'testdb'

    def setUp(self):
        super(CouchDbAdapterTest, self).setUp()
        self.resource_path = os.path.join(os.path.dirname(__file__),
                                          "couchdb/")

        def callback(db, info):
            assert db is not None
            assert 'db_name' in info.keys()
            assert info['db_name'] == self.db_name
            self.db = db
            self.stop()
        couchadapter.CouchDbAdapter(
            self.db_name,
            username=options.couchdb_user,
            password=options.couchdb_password,
            resource_path=self.resource_path,
            create=True, callback=callback, ioloop=self.io_loop)
        self.wait()

    def tearDown(self):
        def delete_cb(dele):
            assert 'ok' in dele.keys()
            assert dele['ok'] is True
            self.stop()
        self.db.delete_db(delete_cb)
        self.wait()

    def test_create_delete(self):
        def callback(db, info):
            def delete_cb(dele):
                assert db is not None
                assert 'ok' in info.keys()
                assert 'ok' in dele.keys()
                assert info['ok'] is True
                assert dele['ok'] is True
                self.stop()
            db.delete_db(delete_cb)
        db_name = 'testcreatedb'
        couchadapter.CouchDbAdapter(
            db_name,
            username=options.couchdb_user,
            password=options.couchdb_password,
            create=True, callback=callback,
            resource_path=self.resource_path,
            ioloop=self.io_loop)
        self.wait()

    def test_save_doc(self):
        document = TestDocument()
        document.string_attr = "test attr"
        print "save", document

        def save_cb(doc):
            assert doc['ok'] is True
            self.stop()
        self.db.save_doc(document, save_cb)
        self.wait()

        def get_cb(doc):
            print "get", doc
            for key, value in doc.items():
                if key == '_rev':
                    assert value != document.get(key, '')
                else:
                    assert value == document[key]
            self.stop()
        self.db.get_doc(document._id, TestDocument, get_cb)
        self.wait()


if __name__ == '__main__':
    unittest.main()
