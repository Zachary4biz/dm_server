# author: zac
# create-time: 2019-07-09 16:25
# usage: - 

import time
import functools


# def timeit(func):
#     a = time.time()
#     b = time.time()


def deco_timeit(func):
    """
    @deco_timeit
    def func(a,b):
        c = a+b
        time.sleep(3)
        return c
    func(1,3) # (5, 3.004)
    """
    @functools.wraps(func)
    def wrapper(*args, **kw):
        t0 = time.time()
        result = func(*args, **kw)
        delta = str(round(time.time() - t0, 5) * 1000)+"ms"
        return result, delta
    return wrapper


def timeit(func, *args, **kwargs):
    """
    def func(a,b):
        c = a+b
        time.sleep(3)
        return c
    timeit(func,1,3) # (5, 3.004)
    """
    b = time.time()
    result = func(*args, **kwargs)
    e = time.time()
    return result, round(e - b, 4)



