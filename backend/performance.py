"""Request-stage timings; logs contain durations and sizes, not child data."""
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter

current_metrics = ContextVar("request_metrics", default=None)


def record(name, milliseconds):
    metrics = current_metrics.get()
    if metrics is not None:
        metrics[name] = round(metrics.get(name, 0) + milliseconds, 2)


@contextmanager
def stage(name):
    start = perf_counter()
    try:
        yield
    finally:
        record(name, (perf_counter() - start) * 1000)


def snapshot():
    return dict(current_metrics.get() or {})
