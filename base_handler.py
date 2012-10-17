import tornado
import tornado.web
from tornado.options import options
from stormbase import session
import urllib
import logging
import traceback
import os

from tornado import gen
from tornado import web
from time import time
import json
from stormbase.util import JSONEncoder
from tornado.curl_httpclient import CurlAsyncHTTPClient
from urlparse import urlparse
from tornado.httpclient import AsyncHTTPClient

CACHID = time()


def async_engine(func):
    return web.asynchronous(gen.engine(func))


class ProxyCurlAsyncHTTPClient(CurlAsyncHTTPClient):
    fetch_args = None

    def initialize(self, io_loop=None, max_clients=10,
                   max_simultaneous_connections=None, **kwargs):
        super(ProxyCurlAsyncHTTPClient, self).initialize(
            io_loop,
            max_clients,
            max_simultaneous_connections)
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

    def initialize(self, *args, **kwargs):
        self.db = self.application.db
        self.session = session.Session(self.application.session_manager, self)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.render_method = kwargs.get('render_method', 'html')

    def get_current_user(self):
        userid = self.get_secure_cookie("user")
        user_obj = self.session.get(userid, None)
        logging.debug("LOGINSTATUS: %s, %s" % (userid, user_obj is not None))
        if not userid or not user_obj:
            return None
        return user_obj

    def _default_template_variables(self, kwargs):
        kwargs['options'] = options
        kwargs['static_url'] = self.static_url
        kwargs['url'] = self.url
        kwargs['xsrf_form_html'] = self.xsrf_form_html
        kwargs['xsrf_token'] = self.xsrf_token
        kwargs['add_javascript'] = self.add_javascript
        kwargs['current_user'] = self.current_user

    def end(self, *args, **kwargs):
        if self.render_method == 'html':
            return self.render(*args, **kwargs)
        elif self.render_method == 'json':
            return self.render_json(kwargs)
        raise Exception("Unknown render_method:%s" % self.render_method)

    def render(self, template_name, finish=True, **kwargs):
        self._default_template_variables(kwargs)
        template = self.application.jinja_env.get_template(template_name)
        self.write(template.render(kwargs))
        if finish:
            self.finish()

    def render_string_template(self, string_template, **kwargs):
        self._default_template_variables(kwargs)
        template = self.application.jinja_env.from_string(string_template)
        return template.render(**kwargs).strip()

    def render_json(self, data, finish=True):
        self.write(json.dumps(data, cls=JSONEncoder))
        if finish:
            self.finish()

    def static_url(self, url):
        return urllib.basejoin(options.static_root, url)

    def url(self, url):
        return urllib.basejoin(options.root, url)

    def add_javascript(self, script, cache=True, **kwargs):
        if script.startswith('http'):
            path = script
        else:
            path = urllib.basejoin(options.script_root, script)
        cachestring = ('' if cache or not options.debug
                       else '?cacheid=%s' % CACHID)
        return """<script src="%s%s" type="text/javascript"></script>""" \
            % (path, cachestring)

    #def get_error_html(self, status_code, **kwargs):
    #    self.render('error.html', status_code=status_code,
    #        message=httplib.responses[status_code])

    def error(self, exception):
        try:
            logging.error("Handler Exception:  %s." % str(exception))
            traceback.print_exc()
        except Exception, e:
            print "Error logging." + str(e)
