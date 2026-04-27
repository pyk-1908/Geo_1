import os
import pickle
import redis


class RedisCache:
    """
    Provides synchronous caching functionality using Redis.
    """

    def __init__(self, redis_url="redis://localhost", ttl=360000):
        if os.getenv('REDIS_HOST') is None:
            return
        self.ttl = ttl
        self.redis_url = redis_url
        self.redis = redis.Redis.from_url(self.redis_url, decode_responses=False)

    def get(self, key):
        if os.getenv('REDIS_HOST') is None:
            return None

        key = pickle.dumps(key)
        cached = self.redis.get(key)
        if cached:
            return pickle.loads(cached)
        return None

    def set(self, key, value):
        if os.getenv('REDIS_HOST') is None:
            return
        timetolive = 360000 if len(key) == 3 else self.ttl
        key = pickle.dumps(key)
        value = pickle.dumps(value)
        self.redis.set(key, value, ex=timetolive)

    def empty_cache(self):
        if os.getenv('REDIS_HOST') is None:
            return
        self.redis.flushdb()

    def delete_by_prefix(self, customer):
        if os.getenv('REDIS_HOST') is None:
            return
        for redis_key in self.redis.scan_iter():
            try:
                key_tuple = pickle.loads(redis_key)
                if isinstance(key_tuple, tuple) and key_tuple[1] == customer and len(key_tuple) > 3:
                    self.redis.delete(redis_key)
            except pickle.UnpicklingError:
                pass

    def close(self):
        if os.getenv('REDIS_HOST') is None:
            return
        self.redis.close()