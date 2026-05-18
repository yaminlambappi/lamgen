from functools import wraps
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed

def with_async_retry(attempts=3, wait_time=2):
    def decorator(func):
        @wraps(func)
        @retry(stop=stop_after_attempt(attempts), wait=wait_fixed(wait_time))
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator
