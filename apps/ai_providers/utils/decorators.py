from functools import wraps
from tenacity import retry, stop_after_attempt, wait_fixed

def with_retry(attempts=3, wait_time=2):
    def decorator(func):
        @wraps(func)
        @retry(stop=stop_after_attempt(attempts), wait=wait_fixed(wait_time))
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
