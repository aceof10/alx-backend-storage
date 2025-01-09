#!/usr/bin/env python3
"""
    Create a Cache class. In the __init__ method, store an instance of the
    Redis client as a private variable named _redis (using redis.Redis())
    and flush the instance using flushdb.

    Create a store method that takes a data argument and returns a string.
    The method should generate a random key (e.g. using uuid), store the input
    data in Redis using the random key and return the key.

    Create a get method that take a key string argument and an optional
    Callable argument named fn. This callable will be used to convert
    the data back to the desired format.

    Implement a system to count how many times methods of the Cache class
    are called.

    Will define a call_history decorator to store the history of inputs
    and outputs for a particular function.
"""
from functools import wraps
from typing import Any, Callable, Union
import redis
import uuid


def count_calls(method: Callable) -> Callable:
    """
      tracks number of calls  in  Cache class
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs) -> Any:
        """
          returns the method
        """
        if isinstance(self._redis, redis.Redis):
            self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)

    return wrapper


def call_history(method: Callable) -> Callable:
    """
      stores history of inputs and outputs
    """
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        """
          returns the method's output
        """
        in_key = '{}:inputs'.format(method.__qualname__)
        out_key = '{}:outputs'.format(method.__qualname__)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(in_key, str(args))
        output = method(self, *args, **kwargs)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(out_key, output)
        return output
    return invoker


def replay(fn: Callable) -> None:
    """
      Cache call history
    """
    if fn is None or not hasattr(fn, '__self__'):
        return
    redis_store = getattr(fn.__self__, '_redis', None)
    if not isinstance(redis_store, redis.Redis):
        return
    fxn_name = fn.__qualname__
    in_key = '{}:inputs'.format(fxn_name)
    out_key = '{}:outputs'.format(fxn_name)
    fxn_call_count = 0
    if redis_store.exists(fxn_name) != 0:
        fxn_call_count = int(redis_store.get(fxn_name))
    print('{} was called {} times:'.format(fxn_name, fxn_call_count))
    fxn_inputs = redis_store.lrange(in_key, 0, -1)
    fxn_outputs = redis_store.lrange(out_key, 0, -1)
    for fxn_input, fxn_output in zip(fxn_inputs, fxn_outputs):
        print('{}(*{}) -> {}'.format(
            fxn_name,
            fxn_input.decode("utf-8"),
            fxn_output,
        ))


class Cache:
    """
      Cache class
    """

    def __init__(self) -> None:
        self._redis = redis.Redis()
        self._redis.flushdb(True)

    @call_history
    @count_calls
    def store(self, data:  Union[str, bytes, int, float]) -> str:
        """
          generates and returns a key
        """
        data_key = str(uuid.uuid4())
        self._redis.set(data_key, data)
        return data_key

    def get(
            self,
            key: str,
            fn: Callable = None,
            ) -> Union[str, bytes, int, float]:
        """
            returns a value from a Redis data storage
        """
        data = self._redis.get(key)
        return fn(data) if fn is not None else data

    def get_str(self, key: str) -> str:
        """
            returns a string value
        """
        return self.get(key, lambda x: x.decode('utf-8'))

    def get_int(self, key: str) -> int:
        """
            a Redis data storage
        """
        return self.get(key, lambda x: int(x))
