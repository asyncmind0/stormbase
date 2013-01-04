import pystache


class MustacheRenderer(object):
    def render_string_template(self, string_template, **kwargs):
        return pystache.render(string_template, kwargs)
        
    def render(self, template_name, **kwargs):
        return pystache.render_path(template_name, kwargs)


class JinjaRenderer(object):
    def __init__(self, jinja_env):
        self.jinja_env = jinja_env
    def render(self, template_name, **kwargs):
        template = self.jinja_env.get_template(template_name)
        return template.render(kwargs)
    def render_string_template(self, string_template, **kwargs):
        template = self.application.jinja_env.from_string(string_template)
        return template.render(**kwargs).strip()
