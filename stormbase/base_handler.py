import tornado
import tornado.web
from tornado.options import options
from stormbase import session
from stormbase.util import dump_json, load_json
import urllib
import logging
import traceback
import os
import marshal

try:
    import pylibmc as memcache
except ImportError:
    import memcache

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from tornado import gen
from tornado import web
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.httpclient import AsyncHTTPClient
from tornado import stack_context
from .renderers import MustacheRenderer, JinjaRenderer


def async_engine(func):
    return web.asynchronous(gen.engine(func))


class ProxyCurlAsyncHTTPClient(CurlAsyncHTTPClient):
    fetch_args = None

    def initialize(self, io_loop=None, max_clients=10,
                   **kwargs):
        super(ProxyCurlAsyncHTTPClient, self).initialize(
            io_loop,
            max_clients)
        self.fetch_args = kwargs

    def fetch(self, request, callback, **kwargs):
        kwargs.update(self.fetch_args)
        if 'no_proxy' in kwargs.keys():
            logging.debug("found no_proxy:%s" % str(kwargs['no_proxy']))
            if isinstance(request, str):
                if urlparse(request).hostname in kwargs['no_proxy']:
                    del kwargs['proxy_host']
                    del kwargs['proxy_port']
            del kwargs['no_proxy']
        super(
            ProxyCurlAsyncHTTPClient, self).fetch(request, callback, **kwargs)

proxy_url = os.getenv('http_proxy', '')

if proxy_url:
    parsed = urlparse(proxy_url)
    AsyncHTTPClient.configure(
        ProxyCurlAsyncHTTPClient, proxy_host=parsed.hostname,
        proxy_port=parsed.port, proxy_username=parsed.username,
        proxy_password=parsed.password, no_proxy=['localhost'])


class StormBaseHandler(tornado.web.RequestHandler):
    session = None
    params = {}
    user_class = None

    def initialize(self, *args, **kwargs):
        self.db = self.application.db
        if hasattr(self.application, 'session_manager'):
            self.session = session.Session(
                self.application.session_manager, self)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.render_method = kwargs.get('render_method', 'html')
        render_engine = kwargs.get('render_engine', 'jinja')
        self.render_engine = JinjaRenderer(self, self.application.jinja_env) \
            if render_engine == 'jinja' \
            and hasattr(self.application, 'jinja_env') \
            else MustacheRenderer(
                self, [self.application.settings['template_path']],
                not options.debug)
        self.params = kwargs

    def is_admin(self):
        return (True if self.current_user and
                self.current_user.email in
                options.admin_emails else False)

    def end(self, *args, **kwargs):
        if self.render_method == 'html':
            return self.render(self.template or args[0], *args[1:], **kwargs)
        elif self.render_method == 'json':
            return self.render_json(kwargs)
        elif self.render_method == 'string':
            return self.render_string_template(self.template_string or args[0],
                                               *args[1:], **kwargs)
        elif hasattr(self, self.render_method):
            render_method = getattr(self, self.render_method)
            if hasattr(render_method, '__call__'):
                return render_method(*args, **kwargs)
        raise Exception("Unknown render_method:%s" % self.render_method)

    def render(self, template_name, finish=True, **kwargs):
        self.write(self.render_engine.render(template_name, **kwargs))
        if finish:
            self.finish()

    def render_string_template(self, string_template, finish=True, **kwargs):
        self.write(
            self.render_engine.render_string_template(
                string_template, **kwargs))
        if finish:
            self.finish()

    def render_json(self, data, finish=True):
        self.write(dump_json(data))
        if finish:
            self.finish()

    def static_url(self, url):
        return urllib.basejoin(options.static_root, url)

    def get_url(self, url, full=False):
        path = urllib.basejoin(options.root, url)
        return ((self.request.protocol + '://' +
                self.request.host + path) if full else path)

    # def get_error_html(self, status_code, **kwargs):
    #    self.render('error.html', status_code=status_code,
    #        message=httplib.responses[status_code])
    def error(self, exception):
        try:
            logging.error("Handler Exception:  %s." % str(exception))
            traceback.print_exc()
        except Exception as e:
            print("Error logging." + str(e))

    def memcache_set(self, key, value, expiry=0, compress=0):
        _data = marshal.dumps(value)
        mc = memcache.Client(options.memcached_addresses, binary=True)
        mc.set(key, _data, expiry, compress)

    def memcache_get(self, key):
        try:
            mc = memcache.Client(options.memcached_addresses)
            _data = raw_data = mc.get(key)
            if raw_data is not None:
                _data = marshal.loads(raw_data)
            if isinstance(_data, type({})):
                return _data
            else:
                return {}
        except IOError as e:
            logging.exception(e)
            return {}

    def get_real_ip(self, geolocate=True):
        try:
            self.real_ip = self.request.headers.get(
                'X-Real-Ip',
                self.request.headers.get('X-Forwarded-For', None))
            logging.info(
                "Request from " + str(self.real_ip) + str(self.__class__))
            if geolocate:
                geo_key = "geo_%s" % self.real_ip
                cached_geo = self.memcache_get(geo_key)
                if cached_geo:
                    logging.info(cached_geo)
                else:
                    def handle_request(responses):
                        geo = load_json(responses.body)
                        self.memcache_set(geo_key, geo)
                        logging.info(geo)
                    http_client = CurlAsyncHTTPClient()
                    # need to make this a external configuration
                    http_client.fetch("http://freegeoip.net/json/%s" %
                                      self.real_ip,
                                      callback=handle_request,
                                      request_timeout=2,
                                      connect_timeout=2)
        except Exception as e:
            self.error(e)

    @stack_context.contextlib.contextmanager
    def on_async_error(self):
        try:
            yield
        except Exception as e:
            logging.error("exception in asynchronous operation", exc_info=True)
            self.write(str(e))

    def write_error(self, status_code, **kwargs):
        import traceback
        import inspect
        from cgi import escape
        exc_info = kwargs["exc_info"]
        trace_info = ''.join(["%s<br/>" % escape(line) for line in
                              traceback.format_exception(*exc_info)])
        locals_info = '<br>'.join([ ":".join(map(escape,map(str,v))) for v in
                               inspect.trace()[-1][0].f_locals.iteritems()])
        request_info = ''.join(["<strong>%s</strong>: %s<br/>" %
                                (escape(k), escape(str(self.request.__dict__[k])))
                                for k in self.request.__dict__.keys()])
        error = exc_info[1]
        self.write(self.render_engine.render_error(error=error,
                                                   status_code=status_code,
                                                   trace_info=trace_info,
                                                   locals_info=locals_info,
                                                   request_info=request_info))
        self.finish()

    @property
    def query_dict(self):
        qd = {}
        for key,value in self.request.arguments.iteritems():
            qd[key] = value[0] if len(value) == 1 else value
        return qd
            


class ErrorHandler(StormBaseHandler):
    """Generates an error response with status_code for all requests."""
    def __init__(self, application, request, status_code):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.set_status(status_code)

    def prepare(self):
        raise tornado.web.HTTPError(self._status_code)

## override the tornado.web.ErrorHandler with our default ErrorHandler
tornado.web.ErrorHandler = ErrorHandler


def get_static_handlers():
    static_root = options.static_root
    static_root = (static_root[1:] if
                   static_root.startswith(os.path.sep) else static_root)
    cwd = os.getcwd()
    static_root = os.path.join(cwd, static_root)

    return [
        (r'/static/javascript/%s/(.*)' % options.site_name,
         tornado.web.StaticFileHandler,
         {'path': os.path.join(
             cwd, 'src/javascript/%s/' % options.site_name)}),
        (r'/static/vendor/(.*)', tornado.web.StaticFileHandler,
         {'path': os.path.join(cwd, '../../var/static/vendor')}),
        (r'/static/common/(.*)$', tornado.web.StaticFileHandler,
         {'path': os.path.join(cwd, '../../var/static')}),
        (r'/static/(.*)', tornado.web.StaticFileHandler,
         {'path': static_root}),
        (r'/favicon.ico(.*)', tornado.web.StaticFileHandler,
         {'path': os.path.join(static_root, 'img/favicon.ico')})
    ]
