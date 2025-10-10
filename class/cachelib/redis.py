import typing as _t

from cachelib.base import BaseCache
from cachelib.serializers import RedisSerializer


class RedisCache(BaseCache):
    """Uses the Redis key-value store as a cache backend.

    The first argument can be either a string denoting address of the Redis
    server or an object resembling an instance of a redis.Redis class.

    Note: Python Redis API already takes care of encoding unicode strings on
    the fly.

    :param host: address of the Redis server or an object which API is
                 compatible with the official Python Redis client (redis-py).
    :param port: port number on which Redis server listens for connections.
    :param password: password authentication for the Redis server.
    :param db: db (zero-based numeric index) on Redis Server to connect.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`. A timeout of
                            0 indicates that the cache never expires.
    :param key_prefix: A prefix that should be added to all keys.

    Any additional keyword arguments will be passed to ``redis.Redis``.
    """

    _read_client: _t.Any = None
    _write_client: _t.Any = None
    serializer = RedisSerializer()

    def __init__(
        self,
        host: _t.Any = "localhost",
        port: int = 6379,
        password: _t.Optional[str] = None,
        db: int = 0,
        default_timeout: int = 300,
        key_prefix: _t.Optional[str] = None,
        **kwargs: _t.Any
    ):
        BaseCache.__init__(self, default_timeout)
        if host is None:
            raise ValueError("RedisCache host parameter may not be None")
        if isinstance(host, str):
            try:
                import redis
            except ImportError as err:
                raise RuntimeError("no redis module found") from err
            if kwargs.get("decode_responses", None):
                raise ValueError("decode_responses is not supported by RedisCache.")
            self._write_client = self._read_client = redis.Redis(
                host=host, port=port, password=password, db=db, **kwargs
            )
        else:
            self._read_client = self._write_client = host
        self.key_prefix = key_prefix or ""

    def _normalize_timeout(self, timeout: _t.Optional[int]) -> int:
        """Normalize timeout by setting it to default of 300 if
        not defined (None) or -1 if explicitly set to zero.

        :param timeout: timeout to normalize.
        """
        timeout = BaseCache._normalize_timeout(self, timeout)
        if timeout == 0:
            timeout = -1
        return timeout

    def get(self, key: str) -> _t.Any:
        return self.serializer.loads(self._read_client.get(self.key_prefix + key))

    def get_many(self, *keys: str) -> _t.List[_t.Any]:
        if self.key_prefix:
            prefixed_keys = [self.key_prefix + key for key in keys]
        else:
            prefixed_keys = list(keys)
        return [self.serializer.loads(x) for x in self._read_client.mget(prefixed_keys)]

    def set(self, key: str, value: _t.Any, timeout: _t.Optional[int] = None) -> _t.Any:
        timeout = self._normalize_timeout(timeout)
        dump = self.serializer.dumps(value)
        if timeout == -1:
            result = self._write_client.set(name=self.key_prefix + key, value=dump)
        else:
            result = self._write_client.setex(
                name=self.key_prefix + key, value=dump, time=timeout
            )
        return result

    def add(self, key: str, value: _t.Any, timeout: _t.Optional[int] = None) -> _t.Any:
        timeout = self._normalize_timeout(timeout)
        dump = self.serializer.dumps(value)
        created = self._write_client.setnx(name=self.key_prefix + key, value=dump)
        # handle case where timeout is explicitly set to zero
        if created and timeout != -1:
            self._write_client.expire(name=self.key_prefix + key, time=timeout)
        return created

    def set_many(
        self, mapping: _t.Dict[str, _t.Any], timeout: _t.Optional[int] = None
    ) -> _t.List[_t.Any]:
        timeout = self._normalize_timeout(timeout)
        # Use transaction=False to batch without calling redis MULTI
        # which is not supported by twemproxy
        pipe = self._write_client.pipeline(transaction=False)

        for key, value in mapping.items():
            dump = self.serializer.dumps(value)
            if timeout == -1:
                pipe.set(name=self.key_prefix + key, value=dump)
            else:
                pipe.setex(name=self.key_prefix + key, value=dump, time=timeout)
        results = pipe.execute()
        res = zip(mapping.keys(), results)  # noqa: B905
        return [k for k, was_set in res if was_set]

    def delete(self, key: str) -> bool:
        return bool(self._write_client.delete(self.key_prefix + key))

    def delete_many(self, *keys: str) -> _t.List[_t.Any]:
        if not keys:
            return []
        if self.key_prefix:
            prefixed_keys = [self.key_prefix + key for key in keys]
        else:
            prefixed_keys = [k for k in keys]
        self._write_client.delete(*prefixed_keys)
        return [k for k in prefixed_keys if not self.has(k)]

    def has(self, key: str) -> bool:
        return bool(self._read_client.exists(self.key_prefix + key))

    def clear(self) -> bool:
        status = 0
        if self.key_prefix:
            keys = self._read_client.keys(self.key_prefix + "*")
            if keys:
                status = self._write_client.delete(*keys)
        else:
            status = self._write_client.flushdb()
        return bool(status)

    def inc(self, key: str, delta: int = 1) -> _t.Any:
        return self._write_client.incr(name=self.key_prefix + key, amount=delta)

    def dec(self, key: str, delta: int = 1) -> _t.Any:
        return self._write_client.incr(name=self.key_prefix + key, amount=-delta)
