from stormbase.debug import debug as sj_debug
import tornado
import tornado.web
from tornado.options import options
from stormbase import session
import httplib
import logging
import traceback

from tornado import gen
from tornado import web


def async_engine(func):
    return web.asynchronous(gen.engine(func))

class StormBaseHandler(tornado.web.RequestHandler):
    def initialize(self,*args, **kwargs):
        self.db = self.application.db

    def __init__(self, *argc, **argkw):
        super(StormBaseHandler, self).__init__(*argc, **argkw)
        self.session = session.Session(self.application.session_manager, self)

    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)


    def _default_template_variables(self, kwargs):
        kwargs['options']=options
        kwargs['static_url']=self.static_url
        kwargs['url']=self.url
        kwargs['xsrf_form_html']=self.xsrf_form_html
        kwargs['xsrf_token']=self.xsrf_token

    def render(self, template_name, **kwargs):
        self._default_template_variables(kwargs)
        template = self.application.jinja_env.get_template(template_name)
        self.write(template.render(kwargs))

    def render_string_template(self, string_template, **kwargs):
        self._default_template_variables(kwargs)
        template = self.application.jinja_env.from_string(string_template)
        return template.render(**kwargs).strip()

    def render_json(self, data):
        return self.write(tornado.escape.json_encode(data))

    def static_url(self,url):
        STATIC_ROOT = options.static_root
        if STATIC_ROOT.endswith('/') and url.startswith('/'):
            return STATIC_ROOT+url[1:]
        return STATIC_ROOT+url

    def url(self,url):
        #return '/macrohms/static/'+url
        ROOT = options.root
        #debug()
        if ROOT.endswith('/') and url.startswith('/'):
            return ROOT+url[1:]
        return ROOT+url

    def get_error_html(self, status_code, **kwargs):
        self.render('error.html', status_code=status_code,
            message=httplib.responses[status_code])

    def error(self,exception):
        try:
            logging.error("Handler Exception:  %s."% str(exception))
            traceback.print_exc()
        except Exception, e:
            print "Error logging." +str(e)

