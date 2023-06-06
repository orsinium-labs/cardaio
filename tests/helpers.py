from __future__ import annotations

from contextlib import contextmanager
import time


@contextmanager
def duration_between(min_dur: float, max_dur: float):
    start = time.perf_counter()
    yield
    actual_dur = time.perf_counter() - start
    assert min_dur <= actual_dur < max_dur, f'time spent: {actual_dur}'
