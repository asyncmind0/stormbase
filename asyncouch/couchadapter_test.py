from debug import debug as sj_debug
import couchadapter
import unittest
from tornado import gen
from tornado.testing import AsyncHTTPTestCase, AsyncTestCase, LogTrapTestCase

class CouchDbAdapterTest(AsyncTestCase,LogTrapTestCase):
    def setUp(self):
        super(CouchDbAdapterTest,self).setUp()
        db_name = 'testdb'
        def callback(db, info):
            assert db is not None
            assert 'db_name' in info.keys()
            assert info['db_name'] == db_name
            self.db = db
            self.stop()
        couchadapter.CouchDbAdapter(db_name,create=True, callback=callback, ioloop=self.io_loop)
        self.wait()

    def tearDown(self):
        def delete_cb(dele):
            assert 'ok' in dele.keys()
            assert dele['ok'] == True
            pass
        self.db.delete_db(delete_cb)

    @unittest.skip
    def test_create_delete(self):
        def callback(db, info):
            def delete_cb(dele):
                assert db is not None
                assert 'ok' in info.keys()
                assert 'ok' in dele.keys()
                assert info['ok'] == True
                assert dele['ok'] == True
                self.stop()
            db.delete_db(delete_cb)
        db_name = 'testcreatedb'
        couchadapter.CouchDbAdapter(db_name,create=True, callback=callback,
                resource_path = "/home/steven/www/webapps/facebook/couchdb",
                ioloop=self.io_loop)
        self.wait()


    def test_sync_resources(self):
        db_name = 'facebook'
        def callback(db, info):
            print info
            self.stop()
        couchadapter.CouchDbAdapter(db_name,create=True, callback=callback,
                resource_path = "/home/steven/www/webapps/facebook/couchdb",
                ioloop=self.io_loop)
        self.wait()


if __name__ == '__main__':
    unittest.main()
