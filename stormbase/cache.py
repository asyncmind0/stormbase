from pylibmc import Client


class MemcachedAdapter(Client):
    """ Abstraction wrapper around memcaced client
    """
    def __init__(self, memcached_addresses, *args, **kwargs):
        super(MemcachedAdapter, self).__init__(
            memcached_addresses, *args, **kwargs)
