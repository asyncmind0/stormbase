from corduroy import Document
from datetime import datetime
import dateutil

class BaseDocument(Document):
    def __init__(self, *args, **kwargs):
        default = self.__class__.defaults
        # print value
        type_keys = default.keys()
        value = args[0] if len(args) >= 1 else None

        if value is None or not isinstance(value, dict):
            value = {}
        val_keys = value.keys()
        for tkey in type_keys:
            if tkey in val_keys and value[tkey]:
                if isinstance(default[tkey], datetime):
                    if not isinstance(value[tkey], datetime):
                        dt = dateutil.parser.parse(value[tkey])
                        value[tkey] = dt
                else:
                    value[tkey] = type(default[tkey])(value[tkey])
            else:
                value[tkey] = default[tkey]
        super(BaseDocument, self).__init__(value)
        self.doc_type = self.__class__.__name__
