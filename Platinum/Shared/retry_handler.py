"""
retry_handler.py — Retry Decorator (Platinum Tier)
---------------------------------------------------
Provides with_retry() decorator for transient-failure resilience.
Used by Gmail watcher, sync agent, health monitor, etc.

Usage:
  from Shared.retry_handler import with_retry

  @with_retry(max_attempts=3, delay=2.0, exceptions=(IOError, requests.Timeout))
  def fetch_something():
      ...
"""

import time
import functools
from typing import Callable, Type, Tuple


# ── Decorator ─────────────────────────────────────────────────────────────────

def with_retry(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> Callable:
    """
    Decorator that retries the wrapped function on specified exceptions.

    Args:
        max_attempts : total attempts (1 = no retry)
        delay        : seconds before first retry
        backoff      : multiplier for each subsequent retry delay
        exceptions   : tuple of exception types to catch and retry
        on_retry     : optional callback(attempt_number, exc) called before each retry

    Example:
        @with_retry(max_attempts=3, delay=1.0, exceptions=(requests.Timeout,))
        def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            last_exc: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    if on_retry:
                        on_retry(attempt, exc)
                    else:
                        print(f"[retry] {func.__name__} attempt {attempt}/{max_attempts} failed: {exc} — retrying in {wait:.1f}s")
                    time.sleep(wait)
                    wait *= backoff

            raise last_exc  # type: ignore

        return wrapper
    return decorator


# ── Simple call-time helper (no decorator) ────────────────────────────────────

def retry_call(
    func: Callable,
    *args,
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs,
):
    """
    Call func(*args, **kwargs) with retry logic — no decorator needed.

    Example:
        result = retry_call(requests.get, url, timeout=10, max_attempts=3)
    """
    wait = delay
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            print(f"[retry] {func.__name__} attempt {attempt}/{max_attempts}: {exc} — retrying in {wait:.1f}s")
            time.sleep(wait)
            wait *= backoff

    raise last_exc  # type: ignore
