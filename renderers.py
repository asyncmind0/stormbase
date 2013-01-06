from stormbase.util import load_json
from tornado.options import options
import pystache
import urllib
from time import time

CACHID = time()


class BaseRenderer(object):
    def __init__(self, handler):
        self.handler = handler

    def _default_template_variables(self, kwargs):
        kwargs['add_javascript'] = self.add_javascript
        kwargs['add_css'] = self.add_css
        kwargs['request_uri'] = self.handler.request.uri

    def add_css(self, css="", cache=True, vendor=False, **kwargs):
        if css.startswith('http'):
            path = css
        elif vendor:
            path = urllib.basejoin(options.vendor_css_root, css)
        else:
            path = urllib.basejoin(options.static_root, 'css/')
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
            path = urllib.basejoin(options.script_root, script)
        cachestring = ('' if cache or not options.debug
                       else '?cacheid=%s' % CACHID)
        kwargs = " ".join(map(lambda x: "%s=\"%s\"" % x, kwargs.items()))
        kwargs = kwargs.replace("_", "-")
        return """<script src="%s%s" %s type="text/javascript"></script>""" \
            % (path, cachestring, kwargs)


class MustacheRenderer(BaseRenderer):
    def __init__(self, handler, search_dirs):
        super(MustacheRenderer, self).__init__(handler)
        self.renderer = pystache.Renderer(search_dirs=search_dirs)

    def add_options_variables(self, kwargs):
        kwargs['class_options_debug_html'] = 'debug' \
            if options.debug_html else ''
        for option in options:
            kwargs['option_' + option] = getattr(options, option)

    def render_string_template(self, string_template, **kwargs):
        self._default_template_variables(kwargs)
        self.add_options_variables(kwargs)
        return pystache.render(string_template, kwargs)

    def render(self, template_name, context=None, **kwargs):
        #template_name = "".join(template_name.split('.')[:-1])
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
