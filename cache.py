from pylibmc import Client


class MemcachedAdapter(Client):
    """ Abstraction wrapper around memcaced client
    """
    def __init__(self, options, *args, **kwargs):
        super(MemcachedAdapter, self).__init__(
            options.memcached_addresses, *args, **kwargs)
