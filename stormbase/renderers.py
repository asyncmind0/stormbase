from stormbase.util import load_json
from tornado.options import options
import urllib
from time import time
import pickle
import logging

CACHID = time()


class BaseRenderer(object):
    def __init__(self, handler):
        self.handler = handler

    def _default_template_variables(self, kwargs):
        kwargs['request_uri'] = self.handler.request.uri
        kwargs['is_admin'] = self.handler.is_admin()

    def add_css(self, css="", cache=True, vendor=False, **kwargs):
        if css.startswith('http'):
            path = css
        elif vendor:
            path = urllib.basejoin(options.vendor_css_root, css)
        else:
            path = urllib.basejoin(options.static_root, '%s/css/' % options.site_name)
            path = urllib.basejoin(path, css)
        cachestring = ('' if cache or not options.debug
                       else '?cacheid=%s' % CACHID)
        extra_params = ""
        for item in kwargs.iteritems():
            extra_params += '%s="%s" ' % item
        return """<link rel="stylesheet" href="%s%s" type="text/css" %s/>""" \
            % (path, cachestring, extra_params)

    def add_javascript(self, script="", cache=True, vendor=False, **kwargs):
        if script.startswith('http'):
            path = script
        elif vendor:
            path = urllib.basejoin(options.vendor_script_root, script)
        else:
            path = "%s/%s/javascript/%s" % (options.static_root, options.site_name, script)
        cachestring = ('' if cache or not options.debug
                       else '?cacheid=%s' % CACHID)
        kwargs = " ".join(map(lambda x: "%s=\"%s\"" % x, kwargs.items()))
        kwargs = kwargs.replace("_", "-")
        return """<script src="%s%s" %s type="text/javascript"></script>""" \
            % (path, cachestring, kwargs)

from pystache import Renderer as PystacheRenderer
from pystache.renderengine import RenderEngine as PystacheRenderEngine
from pystache.parser import parse
from pystache.parsed import ParsedTemplate
from pystache.context import ContextStack


class CachedRenderEngine(PystacheRenderEngine):
    def render(self, parsed_template, context_stack, delimiters=None):
        if isinstance(parsed_template, ParsedTemplate):
            return parsed_template.render(self, context_stack)
        else:
            return super(CachedRenderEngine, self).render(
                parsed_template, context_stack)


class CachedRenderer(PystacheRenderer):
    mc = None

    def __init__(self, memcached_client, *args, **kwargs):
        super(CachedRenderer, self).__init__(*args, **kwargs)
        self.mc = memcached_client

    def memcache_set(self, key, value, expiry=0, compress=0):
        _data = pickle.dumps(value)
        self.mc.set(key, _data, expiry, compress)

    def memcache_get(self, key):
        try:
            _data = raw_data = self.mc.get(key)
            if raw_data is not None:
                _data = pickle.loads(raw_data)
            return _data
        except IOError as e:
            logging.exception(e)
            return None

    def _make_render_engine(self):
        resolve_context = self._make_resolve_context()
        resolve_partial = self._make_resolve_partial()

        engine = CachedRenderEngine(literal=self._to_unicode_hard,
                                    escape=self._escape_to_unicode,
                                    resolve_context=resolve_context,
                                    resolve_partial=resolve_partial,
                                    to_str=self.str_coerce)
        return engine

    def render_name(self, template_name, *context, **kwargs):
        try:
            parsed_template = None
            cache_key = "%s_template_%s" % (options.site_name, template_name)
            parsed_template = self.memcache_get(cache_key)
            if not parsed_template:
                loader = self._make_loader()
                template = loader.load_name(template_name)
                template = self._to_unicode_hard(template)
                parsed_template = parse(template, None)
                self.memcache_set(cache_key, parsed_template)

            stack = ContextStack.create(*context, **kwargs)
            self._context = stack
            engine = self._make_render_engine()
            return parsed_template.render(engine, stack)
        except Exception as e:
            logging.exception(e)
            return e.message


class MustacheRenderer(BaseRenderer):
    def __init__(self, handler, search_dirs, caching=True):
        super(MustacheRenderer, self).__init__(handler)
        if caching:
            self.renderer = CachedRenderer(
                handler.application.cache,
                search_dirs=search_dirs)
        else:
            self.renderer = PystacheRenderer(search_dirs=search_dirs)

    def _default_template_variables(self, kwargs):
        super(MustacheRenderer, self)._default_template_variables(kwargs)
        kwargs['xsrf_form_html'] = self.handler.xsrf_form_html()

    def add_options_variables(self, kwargs):
        kwargs['class_options_debug_html'] = 'debug' \
            if options.debug_html else ''
        kwargs['js_debug'] = 'true' \
            if options.debug else 'false'
        for option in options._options:
            kwargs['option_' + option] = getattr(options, option)

    def render_string_template(self, string_template, **kwargs):
        self._default_template_variables(kwargs)
        self.add_options_variables(kwargs)
        return self.renderer.render(string_template, kwargs)

    def render(self, template_name, context=None, **kwargs):
        # template_name = "".join(template_name.split('.')[:-1])
        self._default_template_variables(kwargs)
        self.add_options_variables(kwargs)
        kwargs['block_css'] = self.block_css
        kwargs['block_javascript'] = self.block_javascript
        return self.renderer.render_name(
            template_name, context or self.handler, **kwargs)

    def block_css(self, text, *args, **kwargs):
        css_includes = load_json(text)
        csses = []
        for css_args in css_includes:
            csses.append(self.add_css(**css_args))
        return "\n".join(csses)

    def block_javascript(self, text, *args, **kwargs):
        js_includes = load_json(text)
        jses = []
        for js_args in js_includes:
            jses.append(self.add_javascript(**js_args))
        return "\n".join(jses)

    def render_error(self, *args, **kwargs):
        kwargs['option_debug?'] = options.debug
        error_template = self.renderer.render_name(
            "error", self.handler, *args, **kwargs)

        return self.render("base", block_content=error_template)


class JinjaRenderer(BaseRenderer):
    def __init__(self, handler, jinja_env):
        super(JinjaRenderer, self).__init__(handler)
        self.jinja_env = jinja_env

    def _default_template_variables(self, kwargs):
        super(JinjaRenderer, self)._default_template_variables(kwargs)
        kwargs['add_javascript'] = self.add_javascript
        kwargs['add_css'] = self.add_css
        kwargs['session'] = self.handler.session
        kwargs['options'] = options
        kwargs['settings'] = self.handler.application.settings
        kwargs['get_url'] = self.handler.get_url
        kwargs['xsrf_token'] = self.handler.xsrf_token
        kwargs['xsrf_form_html'] = self.handler.xsrf_form_html
        kwargs.update(self.handler.get_template_namespace())

    def render(self, template_name, **kwargs):
        self._default_template_variables(kwargs)
        template = self.jinja_env.get_template(template_name)
        return template.render(kwargs)

    def render_string_template(self, string_template, **kwargs):
        self._default_template_variables(kwargs)
        template = self.application.jinja_env.from_string(string_template)
        return template.render(**kwargs).strip()

    def render_error(self, *args, **kwargs):
        return self.render("error.html", *args, **kwargs)
