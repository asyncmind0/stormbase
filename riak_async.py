import functools
from tornado import ioloop
from tornado import iostream
import json
import socket
import struct
import riak_pb
from tornado import gen
from uuid import uuid4
from util import dump_json, load_json

from riak import RiakError
from riak.mapreduce import RiakLink
from riak.riak_index_entry import RiakIndexEntry
from riak.metadata import (
    MD_DELETED,
    MD_CHARSET,
    MD_CTYPE,
    MD_ENCODING,
    MD_INDEX,
    MD_LASTMOD,
    MD_LASTMOD_USECS,
    MD_LINKS,
    MD_USERMETA,
    MD_VTAG,
)

## Protocol codes
MSG_CODE_ERROR_RESP = 0
MSG_CODE_PING_REQ = 1
MSG_CODE_PING_RESP = 2
MSG_CODE_GET_CLIENT_ID_REQ = 3
MSG_CODE_GET_CLIENT_ID_RESP = 4
MSG_CODE_SET_CLIENT_ID_REQ = 5
MSG_CODE_SET_CLIENT_ID_RESP = 6
MSG_CODE_GET_SERVER_INFO_REQ = 7
MSG_CODE_GET_SERVER_INFO_RESP = 8
MSG_CODE_GET_REQ = 9
MSG_CODE_GET_RESP = 10
MSG_CODE_PUT_REQ = 11
MSG_CODE_PUT_RESP = 12
MSG_CODE_DEL_REQ = 13
MSG_CODE_DEL_RESP = 14
MSG_CODE_LIST_BUCKETS_REQ = 15
MSG_CODE_LIST_BUCKETS_RESP = 16
MSG_CODE_LIST_KEYS_REQ = 17
MSG_CODE_LIST_KEYS_RESP = 18
MSG_CODE_GET_BUCKET_REQ = 19
MSG_CODE_GET_BUCKET_RESP = 20
MSG_CODE_SET_BUCKET_REQ = 21
MSG_CODE_SET_BUCKET_RESP = 22
MSG_CODE_MAPRED_REQ = 23
MSG_CODE_MAPRED_RESP = 24
MSG_CODE_INDEX_REQ = 25
MSG_CODE_INDEX_RESP = 26
MSG_CODE_SEARCH_QUERY_REQ = 27
MSG_CODE_SEARCH_QUERY_RESP = 28

RIAKC_RW_ONE = 4294967294
RIAKC_RW_QUORUM = 4294967293
RIAKC_RW_ALL = 4294967292
RIAKC_RW_DEFAULT = 4294967291
from riak.transports.transport import RiakTransport


class RiakAsyncClient(RiakTransport):
    @gen.engine
    def __init__(self, client_id=None, callback=None):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = iostream.IOStream(self.s)
        yield gen.Task(self.stream.connect, ("localhost", 8087))
        args, kwargs = yield gen.Task(self.get_server_info)
        code, self._server_info = args
        self._client_id = client_id
        self._multi_msgs = []
        callback(self, self._server_info)

    def encode_msg(self, msg_code, msg):
        str = msg.SerializeToString()
        slen = len(str)
        hdr = struct.pack("!iB", 1 + slen, msg_code)
        return hdr + str

    def send_msg_code(self, msgcode, expected=None, callback=None):
        msg = struct.pack("!iB", 1, msgcode)
        self.send_pkt(msg, callback)

    def send_pkt(self, msg, callback=None):
        self.stream.write(msg)
        on_msglen = functools.partial(self.on_msglen, callback=callback)
        self.stream.read_bytes(4, on_msglen)

    def send_msg(self, msg_code, msg, expect, callback=None):
        msg = self.encode_msg(msg_code, msg)
        self.send_pkt(msg, callback)

    @gen.engine
    def send_msg_multi(self, msg_code, msg, expect, callback=None):
        (code, msg), _ = yield gen.Task(self.send_pkt,
                                        self.encode_msg(msg_code, msg))
        while not msg.HasField("done") and not msg.done:
            self._multi_msgs.append(msg)
            msg_len = yield gen.Task(self.stream.read_bytes, 4)
            (code, msg), _ = yield gen.Task(self.on_msglen, msg_len)
        multi_msgs = self._multi_msgs
        self._multi_msgs = []
        callback(multi_msgs)

    def on_multi_msg(self, msg, callback=None):
        self._multi_msgs.append(msg)
        if msg.HasField("done") and msg.done:
            multi_msgs = self._multi_msgs
            self._multi_msgs = []
            callback(multi_msgs)

    def on_msglen(self, data, callback=None):
        msglen, = struct.unpack('!i', data)
        on_read_pkt = functools.partial(self.on_read_pkt, callback=callback)
        self.stream.read_bytes(msglen, on_read_pkt)

    def on_read_pkt(self, data, expect=None, callback=None):
        msg_code, = struct.unpack("B", data[:1])
        pkt = data[1:]
        msg = None
        #if msg_code == MSG_CODE_PING_RESP:
        #    msg = None
        #elif msg_code == MSG_CODE_GET_SERVER_INFO_RESP:
        #    msg = riak_pb.RpbGetServerInfoResp()
        #    msg.ParseFromString(pkt)
        if msg_code == MSG_CODE_ERROR_RESP:
            msg = riak_pb.RpbErrorResp()
            msg.ParseFromString(pkt)
            raise Exception(msg.errmsg)
        elif msg_code == MSG_CODE_PING_RESP:
            msg = None
        elif msg_code == MSG_CODE_GET_SERVER_INFO_RESP:
            msg = riak_pb.RpbGetServerInfoResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_GET_CLIENT_ID_RESP:
            msg = riak_pb.RpbGetClientIdResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_SET_CLIENT_ID_RESP:
            msg = None
        elif msg_code == MSG_CODE_GET_RESP:
            msg = riak_pb.RpbGetResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_PUT_RESP:
            msg = riak_pb.RpbPutResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_DEL_RESP:
            msg = None
        elif msg_code == MSG_CODE_LIST_KEYS_RESP:
            msg = riak_pb.RpbListKeysResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_LIST_BUCKETS_RESP:
            msg = riak_pb.RpbListBucketsResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_GET_BUCKET_RESP:
            msg = riak_pb.RpbGetBucketResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_SET_BUCKET_RESP:
            msg = None
        elif msg_code == MSG_CODE_MAPRED_RESP:
            msg = riak_pb.RpbMapRedResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_INDEX_RESP:
            msg = riak_pb.RpbIndexResp()
            msg.ParseFromString(pkt)
        elif msg_code == MSG_CODE_SEARCH_QUERY_RESP:
            msg = riak_pb.RpbSearchQueryResp()
            msg.ParseFromString(pkt)
        else:
            raise Exception("unknown msg code %s" % msg_code)
        #if expect and msg_code != expect:
        #    raise RiakError("unexpected protocol buffer message code: %d"
        #                    % msg_code)
        callback(msg_code, msg)

    def get_encoded_data(self, data):
        return dump_json(data)

    ## RiakTransport API IMPLEMENTATION ####################################

    # FeatureDetection API
    def _server_version(self):
        return self._server_info['server_version']

    def translate_rw_val(self, rw):
        val = self.rw_names.get(rw)
        if val is None:
            return rw
        return val

    @gen.engine
    def ping(self, callback=None):
        args, kwargs = yield gen.Task(self.send_msg_code, MSG_CODE_PING_REQ)
        if callback:
            callback(*args, **kwargs)

    @gen.engine
    def get_server_info(self, callback=None):
        """
        Get information about the server
        """
        code, resp = yield gen.Task(self.send_msg_code,
                                    MSG_CODE_GET_SERVER_INFO_REQ)
        code, resp = code
        callback(code, {'node': resp.node,
                        'server_version': resp.server_version})

    @gen.engine
    def get_client_id(self, callback=None):
        """
        Get the client id used by this connection
        """
        args, kwargs = yield gen.Task(self.send_msg_code,
                                      MSG_CODE_GET_CLIENT_ID_REQ,
                                      MSG_CODE_GET_CLIENT_ID_RESP)
        if callback:
            callback(*args, **kwargs)

    @gen.engine
    def set_client_id(self, client_id, callback=None):
        """
        Set the client id used by this connection
        """
        req = riak_pb.RpbSetClientIdReq()
        req.client_id = client_id

        msg_code, resp = yield gen.Task(self.send_msg,
                                        MSG_CODE_SET_CLIENT_ID_REQ, req,
                                        MSG_CODE_SET_CLIENT_ID_RESP)

        # Using different client_id values across connections is a bad idea
        # since you never know which connection you might use for a given
        # API call. Setting the client_id manually (rather than as part of
        # the transport construction) can be error-prone since the connection
        # could drop and be reinstated using self._client_id.
        #
        # To minimize the potential impact of variant client_id values across
        # connections, we'll store this new client_id and use it for all
        # future connections.
        self._client_id = client_id

        if callback:
            callback(True)

    @gen.engine
    def get(self, bucket_name, key, r=None, pr=None, vtag=None, callback=None):
        """
        Serialize get request and deserialize response
        """
        if vtag is not None:
            raise RiakError("PB transport does not support vtags")

        req = riak_pb.RpbGetReq()
        if r:
            req.r = self.translate_rw_val(r)
        if self.quorum_controls() and pr:
            req.pr = self.translate_rw_val(pr)

        if self.tombstone_vclocks():
            req.deletedvclock = 1

        req.bucket = bucket_name
        req.key = key

        # An expected response code of None implies "any response is valid".
        args, kwargs = yield gen.Task(
            self.send_msg, MSG_CODE_GET_REQ, req, None)
        msg_code, resp = args
        if msg_code == MSG_CODE_GET_RESP:
            contents = []
            for c in resp.content:
                contents.append(self.decode_content(c))
            callback(resp.vclock, contents)
        else:
            callback(None)

    @gen.engine
    def put(self, bucket_name, key, value, metadata=None, vclock=None, w=None,
            dw=None, pw=None, return_body=True,
            if_none_match=False, callback=None, indexes=None):
        """
        Serialize get request and deserialize response
        """

        req = riak_pb.RpbPutReq()
        if w:
            req.w = self.translate_rw_val(w)
        if dw:
            req.dw = self.translate_rw_val(dw)
        if self.quorum_controls() and pw:
            req.pw = self.translate_rw_val(pw)

        if return_body:
            req.return_body = 1
        if if_none_match:
            req.if_none_match = 1

        req.bucket = bucket_name
        req.key = key
        if vclock:
            req.vclock = vclock
        if not metadata:
            metadata = {MD_USERMETA: {},
                        MD_INDEX: [] if not indexes else indexes}
        self.pbify_content(metadata,
                           self.get_encoded_data(value),
                           req.content)

        args, kwargs = yield gen.Task(self.send_msg, MSG_CODE_PUT_REQ, req,
                                      MSG_CODE_PUT_RESP)
        msg_code, resp = args
        if resp is not None:
            contents = []
            for c in resp.content:
                contents.append(self.decode_content(c))
            callback(resp.vclock, contents)

    @gen.engine
    def put_new(self, bucket_name, robj, w=None, dw=None,
                pw=None, return_body=True,
                if_none_match=False, callback=None):
        """Put a new object into the Riak store, returning its (new) key.

        If return_meta is False, then the vlock and metadata return values
        will be None.

        @return (key, vclock, metadata)
        """
        req = riak_pb.RpbPutReq()
        if w:
            req.w = self.translate_rw_val(w)
        if dw:
            req.dw = self.translate_rw_val(dw)
        if self.quorum_controls() and pw:
            req.pw = self.translate_rw_val(pw)

        if return_body:
            req.return_body = 1
        if if_none_match:
            req.if_none_match = 1

        req.bucket = bucket_name

        self.pbify_content(robj.metadata,
                           robj.get_encoded_data(),
                           req.content)

        args, kwargs = yield gen.Task(self.send_msg, MSG_CODE_PUT_REQ, req,
                                      MSG_CODE_PUT_RESP)
        msg_code, resp = args
        if not resp:
            raise RiakError("missing response object")
        if len(resp.content) != 1:
            raise RiakError("siblings were returned from object creation")

        metadata, content = self.decode_content(resp.content[0])
        callback(resp.key, resp.vclock, metadata)

    @gen.engine
    def delete(self, bucket_name, key, vclock=None, rw=None, r=None,
               w=None, dw=None, pr=None, pw=None,
               callback=None):
        """
        Serialize get request and deserialize response
        """

        req = riak_pb.RpbDelReq()
        if rw:
            req.rw = self.translate_rw_val(rw)
        if r:
            req.r = self.translate_rw_val(r)
        if w:
            req.w = self.translate_rw_val(w)
        if dw:
            req.dw = self.translate_rw_val(dw)

        if self.quorum_controls():
            if pr:
                req.pr = self.translate_rw_val(pr)
            if pw:
                req.pw = self.translate_rw_val(pw)

        if self.tombstone_vclocks() and vclock:
            req.vclock = vclock

        req.bucket = bucket_name
        req.key = key

        args, kwargs = yield gen.Task(self.send_msg, MSG_CODE_DEL_REQ, req,
                                      MSG_CODE_DEL_RESP)
        callback(*args, **kwargs)

    @gen.engine
    def get_keys(self, bucket_name, callback=None):
        """
        Lists all keys within a bucket.
        """
        req = riak_pb.RpbListKeysReq()
        req.bucket = bucket_name

        keys = []

        def _handle_response(resp):
            for rkeys in resp:
                map(keys.append, rkeys.keys)

        args = yield gen.Task(self.send_msg_multi,
                              MSG_CODE_LIST_KEYS_REQ,
                              req, MSG_CODE_LIST_KEYS_RESP)
        _handle_response(args)
        callback(keys)

    @gen.engine
    def get_buckets(self, callback=None):
        """
        Serialize bucket listing request and deserialize response
        """
        args, kwargs = yield gen.Task(self.send_msg_code,
                                      MSG_CODE_LIST_BUCKETS_REQ,
                                      MSG_CODE_LIST_BUCKETS_RESP)
        code, resp = args
        callback(resp.buckets)

    @gen.engine
    def get_bucket_props(self, bucket, callback=None):
        """
        Serialize bucket property request and deserialize response
        """
        req = riak_pb.RpbGetBucketReq()
        req.bucket = bucket.name

        args, kwargs = yield gen.Task(self.send_msg, MSG_CODE_GET_BUCKET_REQ,
                                      req, MSG_CODE_GET_BUCKET_RESP)
        code, resp = args
        props = {}
        if resp.props.HasField('n_val'):
            props['n_val'] = resp.props.n_val
        if resp.props.HasField('allow_mult'):
            props['allow_mult'] = resp.props.allow_mult

        callback(props)

    @gen.engine
    def set_bucket_props(self, bucket, props, callback=None):
        """
        Serialize set bucket property request and deserialize response
        """
        req = riak_pb.RpbSetBucketReq()
        req.bucket = bucket.name
        for key in props:
            if key not in ['n_val', 'allow_mult']:
                raise NotImplementedError

        if 'n_val' in props:
            req.props.n_val = props['n_val']
        if 'allow_mult' in props:
            req.props.allow_mult = props['allow_mult']

        args, kwargs = yield gen.Task(self.send_msg, MSG_CODE_SET_BUCKET_REQ,
                                      req, MSG_CODE_SET_BUCKET_RESP)
        callback(*args, **kwargs)

    @gen.engine
    def mapred(self, bucket, query, inputs=None, index=0,
               startkey=None, endkey=None,
               timeout=None, callback=None):
        if not inputs:
            if endkey is None:
                inputs = {'bucket': bucket,
                          'index': index,
                          'key': startkey}
            else:
                inputs = {'bucket': bucket,
                          'index': index,
                          'start': startkey,
                          'end': endkey}
        # Construct the job, optionally set the timeout...
        job = {'inputs': inputs, 'query': query}
        if timeout is not None:
            job['timeout'] = timeout

        content = json.dumps(job)

        req = riak_pb.RpbMapRedReq()
        req.request = content
        req.content_type = "application/json"

        # dictionary of phase results - each content should be an encoded array
        # which is appended to the result for that phase.
        result = {}

        def _handle_response(resp):
            if resp.HasField("phase") and resp.HasField("response"):
                content = json.loads(resp.response)
                if resp.phase in result:
                    result[resp.phase] += content
                else:
                    result[resp.phase] = content
        result = yield gen.Task(self.send_msg_multi, MSG_CODE_MAPRED_REQ,
                                req, MSG_CODE_MAPRED_RESP)

        result = map(lambda x: json.loads(x.response), result)
        #_handle_response(args)
        # If a single result - return the same as the HTTP interface does
        # otherwise return all the phase information
        if not len(result):
            callback(None)
        elif len(result) == 1:
            #callback(result[max(result.keys())])
            callback(result.pop())
        else:
            callback(result)

    @gen.engine
    def get_index(self, bucket, index, startkey, endkey=None, callback=None):
        #if not self.pb_indexes():
        #    return self._get_index_mapred_emu(bucket, index, startkey, endkey)

        req = riak_pb.RpbIndexReq(bucket=bucket, index=index)
        if endkey:
            req.qtype = riak_pb.RpbIndexReq.range
            req.range_min = str(startkey)
            req.range_max = str(endkey)
        else:
            req.qtype = riak_pb.RpbIndexReq.eq
            req.key = str(startkey)

        args, kwargs = yield gen.Task(self.send_msg, MSG_CODE_INDEX_REQ,
                                      req, MSG_CODE_INDEX_RESP)
        callback(*args, **kwargs)

    @gen.engine
    def search(self, index, query, callback=None, **params):
        #if not self.pb_search():
        #    return self._search_mapred_emu(index, query)

        req = riak_pb.RpbSearchQueryReq(index=index, q=query)
        if 'rows' in params:
            req.rows = params['rows']
        if 'start' in params:
            req.start = params['start']
        if 'sort' in params:
            req.sort = params['sort']
        if 'filter' in params:
            req.filter = params['filter']
        if 'df' in params:
            req.df = params['df']
        if 'op' in params:
            req.op = params['op']
        if 'q.op' in params:
            req.op = params['q.op']
        if 'fl' in params:
            if isinstance(params['fl'], list):
                req.fl.extend(params['fl'])
            else:
                req.fl.append(params['fl'])
        if 'presort' in params:
            req.presort = params['presort']

        args, kwargs = yield gen.Task(self.send_msg, MSG_CODE_SEARCH_QUERY_REQ,
                                      req, MSG_CODE_SEARCH_QUERY_RESP)

        code, resp = args
        result = {}
        if resp.HasField('max_score'):
            result['max_score'] = resp.max_score
        if resp.HasField('num_found'):
            result['num_found'] = resp.num_found
        docs = []
        for doc in resp.docs:
            resultdoc = {}
            for pair in doc.fields:
                resultdoc[pair.key] = pair.value
            docs.append(resultdoc)
        result['docs'] = docs
        callback(result)

    def decode_content(self, rpb_content):
        metadata = {}
        if rpb_content.HasField("deleted"):
            metadata[MD_DELETED] = True
        if rpb_content.HasField("content_type"):
            metadata[MD_CTYPE] = rpb_content.content_type
        if rpb_content.HasField("charset"):
            metadata[MD_CHARSET] = rpb_content.charset
        if rpb_content.HasField("content_encoding"):
            metadata[MD_ENCODING] = rpb_content.content_encoding
        if rpb_content.HasField("vtag"):
            metadata[MD_VTAG] = rpb_content.vtag
        links = []
        for link in rpb_content.links:
            if link.HasField("bucket"):
                bucket = link.bucket
            else:
                bucket = None
            if link.HasField("key"):
                key = link.key
            else:
                key = None
            if link.HasField("tag"):
                tag = link.tag
            else:
                tag = None
            links.append(RiakLink(bucket, key, tag))
        if links:
            metadata[MD_LINKS] = links
        if rpb_content.HasField("last_mod"):
            metadata[MD_LASTMOD] = rpb_content.last_mod
        if rpb_content.HasField("last_mod_usecs"):
            metadata[MD_LASTMOD_USECS] = rpb_content.last_mod_usecs
        usermeta = {}
        for usermd in rpb_content.usermeta:
            usermeta[usermd.key] = usermd.value
        if len(usermeta) > 0:
            metadata[MD_USERMETA] = usermeta
        indexes = []
        for index in rpb_content.indexes:
            rie = RiakIndexEntry(index.key, index.value)
            indexes.append(rie)
        if len(indexes) > 0:
            metadata[MD_INDEX] = indexes
        return metadata, rpb_content.value

    def pbify_content(self, metadata, data, rpb_content):
        # Convert the broken out fields, building up
        # pbmetadata for any unknown ones
        for k, v in metadata.iteritems():
            if k == MD_CTYPE:
                rpb_content.content_type = v
            elif k == MD_CHARSET:
                rpb_content.charset = v
            elif k == MD_ENCODING:
                rpb_content.charset = v
            elif k == MD_USERMETA:
                for uk, uv in v.iteritems():
                    pair = rpb_content.usermeta.add()
                    pair.key = uk
                    pair.value = uv
            elif k == MD_INDEX:
                for rie in v:
                    pair = rpb_content.indexes.add()
                    pair.key = rie.get_field()
                    pair.value = rie.get_value()
            elif k == MD_LINKS:
                for link in v:
                    pb_link = rpb_content.links.add()
                    pb_link.bucket = link.get_bucket()
                    pb_link.key = link.get_key()
                    pb_link.tag = link.get_tag()
        rpb_content.value = data


@gen.engine
def on_connect(code, msg):
    print "connect"
    print(yield gen.Task(riakclient.ping))
    print(yield gen.Task(riakclient.put, "test", "one", dict(hello="world")))
    args, kwargs = yield gen.Task(riakclient.get, "test", "one")
    print load_json(args[1][0][1])
    buckets = yield gen.Task(riakclient.get_buckets)
    print "buckets:", buckets
    keys = yield gen.Task(riakclient.get_keys, "test")
    print "keys:", keys
    print(yield gen.Task(riakclient.delete, "test", "one"))

    ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    riakclient = RiakAsyncClient(callback=on_connect)
    ioloop.IOLoop.instance().start()
