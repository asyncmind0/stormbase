import os
import logging
import tornado
from tornado.options import options, define


class LogFilter(logging.Filter):
    def filter(self, rec):
        if rec.module in ['httpclient', 'curl_httpclient'] \
                and rec.levelno == logging.DEBUG:
            return False
        elif rec.msg == '/static/' and rec.levelno == logging.DEBUG:
            return False
        return True


def define_options(other_options=()):
    define("port", default=8000, help="run on the given port", type=int)
    define("debug", default=None, help="run in development mode", type=bool)
    define("testing", default=None, help="run in development mode", type=bool)
    define("debug_html", default=None, help="show html debugging", type=bool)
    define("couchdb_user")
    define("couchdb_password")
    define("couchdb_uri")
    define("couchdb_database")
    define("site_name")
    define("static_root", default='/static/')
    define("script_root", default='/static/javascript')
    define("vendor_script_root", default='/static/vendor/javascript')
    define("vendor_css_root", default='/static/vendor/css')
    define("root")
    define("server_host")
    for opt in other_options:
        define(*opt)


def parse_options(configpath):
    tornado.options.parse_command_line()
    _configfile_ = os.path.join(configpath, "production.conf")
    _core_config_ = os.path.join(configpath, "core.conf")
    if options.testing:
        _configfile_ = os.path.join(configpath, "testing.conf")
    elif options.debug:
        _configfile_ = os.path.join(configpath, "development.conf")
    tornado.options.parse_config_file(_core_config_)
    tornado.options.parse_config_file(_configfile_)
    return tornado.options.parse_command_line()


def configure(configpath="conf", other_options=()):
    define_options(other_options)
    retval = parse_options(configpath)

    logging.basicConfig()
    #logging.getLogger().setLevel(logging.INFO)
    #logging.getLogger('httpclient').setLevel(logging.DEBUG)
    #logging.getLogger('tornado.httpclient').setLevel(logging.INFO)
    #logging.getLogger().addFilter(logging.Filter('httpclient'))
    #logging.getLogger().addHandler(LogHandler())
    logging.getLogger().addFilter(LogFilter())

    logging.debug("Hello NiceDesign")
    logging.info("Hello NiceDesign")
    logging.warning("Hello NiceDesign")
    logging.error("Hello NiceDesign")
    logging.critical("Hello NiceDesign")
    return retval
