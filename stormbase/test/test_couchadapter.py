import os
from datetime import datetime
from stormbase.database.couchdb import CouchDBAdapter, BaseDocument
from stormbase.util import tuct
import unittest
import tornado
from tornado.options import options
from tornado.testing import AsyncTestCase, LogTrapTestCase, gen_test
from corduroy import Database


class TestDocument(BaseDocument):
    """Base User objext
    """
    defaults = tuct(
        string_attr="",
        list_attr=[],
        int_attr=0,
        date_attr=datetime.utcnow())


class CouchDBAdapterTest(AsyncTestCase, LogTrapTestCase):
    db_name = 'testdb'
    def get_new_ioloop(self):
        return tornado.ioloop.IOLoop.instance()

    def setUp(self):
        super(CouchDBAdapterTest, self).setUp()
        self.resource_path = os.path.join(os.path.dirname(__file__),
                                          "couchdb/")
        db = Database(self.db_name,
                      (options.couchdb_user, options.couchdb_password))
        db._couch.create(self.db_name)
        self.adapter = CouchDBAdapter(db)

    def tearDown(self):
        def delete_cb(dele, r):
            assert 'ok' in dele.keys()
            assert dele['ok'] is True
            self.stop()
        self.adapter.db._couch.delete(self.db_name)


    @gen_test
    def test_save_doc(self):
        document = TestDocument()
        document.string_attr = "test attr"
        result, status = yield self.adapter.save(document)
        assert status['ok'] is True
        prev_rev = document._rev
        document.string_attr = "updated"
        result, status = yield self.adapter.save(document)
        assert status['ok'] is True
        doc = yield self.adapter.get(document._id, TestDocument)
        for key, value in doc.items():
            if key == '_rev':
                assert value != prev_rev, \
                    "revision not updated"
            else:
                assert value == document[key]
        assert doc is not None


if __name__ == '__main__':
    unittest.main()
