import tornado
from base_handler import ErrorHandler
## override the tornado.web.ErrorHandler with our default ErrorHandler
tornado.web.ErrorHandler = ErrorHandler
