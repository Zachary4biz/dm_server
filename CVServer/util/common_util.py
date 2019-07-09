# author: zac
# create-time: 2019-07-09 16:25
# usage: - 

import time
import functools


# def timeit(func):
#     a = time.time()
#     b = time.time()


def deco_timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        b = time.time()
        result = func(*args, **kw)
        e = time.time()
        return result, round(e - b, 4)

    return wrapper


def timeit(func):
    b = time.time()
    result = func
    e = time.time()
    return result, round(e - b, 4)
