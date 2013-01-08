from collections import MutableMapping


class ViewResult(list):
    offset = 0


class Document(MutableMapping):
    _data_ = {}

    def __len__(self):
        return self._data_.__len__()

    def __iter__(self):
        return self._data_.__iter__()

    def __getitem__(self, name):
        return self._data_[name]

    def __setitem__(self, name, value):
        self._data_[name] = value

    def __delitem__(self, name):
        del self._data_[name]

    def __getattr__(self, name):
        if name == 'doc_type':
            return self.__class__.__name__
        if name == '_data_' or name.startswith("__"):
            return object.__getattr__(self, name)
        values_dict = self._data_
        if name in values_dict:
            return values_dict[name]
        else:
            return object.__getattr__(self, name)

    def __setattr__(self, name, value):
        if name == '_data_' or name.startswith("__"):
            super(Document, self).__setattr__(name, value)
        else:
            self._data_[name] = value

    @classmethod
    def get_defaults(self):
        raise NotImplementedError()

    def __init__(self, value=None):
        # self._values_dict.update(default)
        default = self.__class__.defaults
        # print value
        type_keys = default.keys()
        if value is None:
            value = {}
        val_keys = value.keys()
        for tkey in type_keys:
            if tkey in val_keys and value[tkey]:
                if isinstance(default[tkey], datetime):
                    if not isinstance(value[tkey], datetime):
                        value[tkey] = dateutil.parser.parse(value[tkey])
                else:
                    value[tkey] = type(default[tkey])(value[tkey])
            else:
                value[tkey] = default[tkey]

        # for key in default:
        #    if key not in value:
        #        value[key] = default[key]
        self._data_ = value

