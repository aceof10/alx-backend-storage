#!/usr/bin/env python3
"""
    Implements a get_page function (prototype: def get_page(url: str) -> str:).
    The core of the function is very simple. It uses the requests module
    to obtain the HTML content of a particular URL and returns it.
"""
import redis
import requests
from functools import wraps
from typing import Callable


redis_store = redis.Redis()


def data_cacher(method: Callable) -> Callable:
    """decorator"""
    @wraps(method)
    def invoker(url) -> str:
        """wrapper function"""
        redis_store.incr(f'count:{url}')
        result = redis_store.get(f'result:{url}')
        if result:
            return result.decode('utf-8')
        result = method(url)
        redis_store.set(f'count:{url}', 0)
        redis_store.setex(f'result:{url}', 10, result)
        return result
    return invoker


@data_cacher
def get_page(url: str) -> str:
    """return url after caching"""
    return requests.get(url).text
