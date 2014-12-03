from pickle import dumps, loads, HIGHEST_PROTOCOL
from werkzeug.contrib.sessions import SessionStore


class MemcachedSessionStore(SessionStore):

    def __init__(self, servers=None, key_prefix="session_%s", default_timeout=300):
        SessionStore.__init__(self)

        if isinstance(servers, (list, tuple)):
            try:
                import memcache
                is_cmemcache = False
                is_pylibmc = False
            except ImportError:
                try:
                    import pylibmc as memcache
                    is_cmemcache = False
                    is_pylibmc = True
                except ImportError:
                    raise RuntimeError(' no memcache module found ')

            if is_cmemcache:
                client = memcache.Client(map(str, servers))
                try:
                    client.debuglog = lambda *a: None
                except Exception:
                    pass
            else:
                if is_pylibmc:
                    client = memcache.Client(servers, binary=False)
                else:
                    client = memcache.Client(servers, False, HIGHEST_PROTOCOL)
        else:
            client = servers

        self._memcache_client = client
        self._memcache_key_prefix = key_prefix
        self._memcache_timeout = default_timeout

    def get_session_key(self, sid):
        if isinstance(sid, unicode):
            sid = sid.encode('utf-8')
        return self._memcache_key_prefix % sid

    def save(self, session):
        key = self.get_session_key(session.sid)
        data = dumps(dict(session))
        self._memcache_client.set(key, data)

    def delete(self, session):
        key = self.get_session_key(session.sid)
        self._memcache_client.delete(key)

    def get(self, sid):
        key = self.get_session_key(sid)
        data = self._memcache_client.get(key)
        if data is not None:
            data = loads(data)
        else:
            data = {}
        return self.session_class(data, sid, False)
