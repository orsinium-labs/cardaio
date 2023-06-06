from __future__ import annotations
import asyncio
import time
from datetime import timedelta
from typing import Awaitable, Callable


Callback = Callable[[], None | Awaitable[None]]


class Heartbeat:
    """Iterator with adjustable delays between iterations.

    Args:
        fastest: The smallest allowed delay. When the delay reaches this value,
            the `faster` method call does nothing.
            Must be non-negative.
        slowest: The highest allowed delay. When the delay reaches this value,
            the `slower` method call does nothing.
            Must be bigger than `fastest`.
        start: The initial delay. If not specified, the average of `fastest`
            and `slowest` will be used.
            Must be between `fastest` and `slowest`.
        ratio: The adjustment ratio for the delay. The default value is 2
            which means the `faster` call will make it go twice faster
            and `slower` call will make it go twice slower.
            Must be bigger than 1.0.
        now: The function returning the current time in seconds.
            Useful for testing or when you want to use `time.perf_counter`.
            By default, `time.monotonic` is used.
    """

    __slots__ = (
        '_callbacks',
        '_delay',
        '_fastest',
        '_now',
        '_prev',
        '_ratio',
        '_slowest',
    )

    def __init__(
        self, *,
        fastest: float | timedelta = timedelta(microseconds=1),
        slowest: float | timedelta = timedelta(minutes=1),
        start: float | timedelta | None = None,
        ratio: float = 2,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        if isinstance(fastest, timedelta):
            fastest = fastest.total_seconds()
        assert fastest >= 0

        if isinstance(slowest, timedelta):
            slowest = slowest.total_seconds()
        assert slowest > fastest

        if isinstance(start, timedelta):
            start = start.total_seconds()
        elif start is None:
            start = (fastest + slowest) / 2
        assert fastest <= start <= slowest
        assert ratio > 1

        self._fastest: float = fastest
        self._slowest: float = slowest
        self._callbacks: list[Callback] = []
        self._now: Callable[[], float] = now
        self._prev: float = -start
        self._ratio: float = ratio
        self._delay: float = start

    def faster(self) -> bool:
        """Make iterations go faster.

        After the method is called, the next iteration
        will have a shorter pause.

        Returns `False` if the `fastest` delay is already reached
        and so the delay cannot be decreased.

        The new delay is determined by `ratio`. For example,
        if current delay is 6 and the ratio is 2, the new delay will be 3.
        """
        if self._delay <= self._fastest:
            return False
        self._delay = max(self._fastest, self._delay / self._ratio)
        return True

    def slower(self) -> bool:
        """Make iterations go slower.

        After the method is called, the next iteration
        will have a longer pause.

        Returns `False` if the `slowest` delay is already reached
        and so the delay cannot be increased.

        The new delay is determined by `ratio`. For example,
        if current delay is 3 and the ratio is 2, the new delay will be 6.
        """
        if self._delay >= self._slowest:
            return False
        self._delay = min(self._slowest, self._delay * self._ratio)
        return True

    @property
    def delay(self) -> float:
        """The current delay between iterations.

        Can be adjusted with `faster` and `slower` methods or be set directly.
        Must be between `fastest` and `slowest` values.
        """
        return self._delay

    @delay.setter
    def delay(self, rate: float) -> None:
        assert self._fastest <= rate <= self._slowest
        self._delay = rate

    def __aiter__(self) -> Heartbeat:
        return self

    def __iter__(self) -> Heartbeat:
        return self

    async def __anext__(self) -> None:
        await self.wait()

    async def wait(self) -> None:
        """Wait for the current delay.

        On the first call, returns immediately.
        On later calls, waits the `delay` seconds since the last `wait` call.
        """
        # Wait in two steps: first half of the time and then the rest.
        # That way, if the machine is suspended during the wait,
        # the delay lag is just half of the delay value at worst.
        await asyncio.sleep(self._get_pause() / 2)
        await asyncio.sleep(self._get_pause())
        self._prev = self._now()

    def __next__(self) -> None:
        time.sleep(self._get_pause() / 2)
        time.sleep(self._get_pause())
        self._prev = self._now()

    def _get_pause(self) -> float:
        elapsed = self._now() - self._prev
        pause = self._delay - elapsed
        if pause <= 0:
            return 0
        return pause
