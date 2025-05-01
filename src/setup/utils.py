


import time
import functools

def retry(max_retries=3, delay=1, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise
                    print(f"Retrying {func.__name__} due to {e} (attempt {retries}/{max_retries})...")
                    time.sleep(delay)
        return wrapper
    return decorator
