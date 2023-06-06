from __future__ import annotations

from datetime import timedelta

import pytest

from cardaio import Heartbeat

from .helpers import duration_between


OK = True
FAIL = False


@pytest.mark.parametrize('given, expected', [
    # fastest
    (dict(fastest=2), OK),
    (dict(fastest=timedelta(seconds=2)), OK),
    (dict(fastest=-1), FAIL),
    (dict(fastest=timedelta(seconds=-3)), FAIL),

    # slowest
    (dict(fastest=2, slowest=6), OK),
    (dict(fastest=timedelta(2), slowest=timedelta(6)), OK),
    (dict(fastest=6, slowest=2), FAIL),
    (dict(slowest=-2), FAIL),
    (dict(fastest=timedelta(6), slowest=timedelta(2)), FAIL),

    # ratio
    (dict(ratio=2), OK),
    (dict(ratio=1.5), OK),
    (dict(ratio=1), FAIL),
    (dict(ratio=1.0), FAIL),
    (dict(ratio=.5), FAIL),
    (dict(ratio=0), FAIL),
    (dict(ratio=-2), FAIL),

    # start
    (dict(fastest=2, start=3, slowest=6), OK),
    (dict(fastest=2, start=timedelta(seconds=3), slowest=6), OK),
    (dict(fastest=2, start=2, slowest=6), OK),
    (dict(fastest=2, start=6, slowest=6), OK),
    (dict(fastest=2, start=1, slowest=6), FAIL),
    (dict(fastest=2, start=-2, slowest=6), FAIL),
    (dict(fastest=2, start=8, slowest=6), FAIL),
])
def test_init_assertions(given: dict, expected: bool) -> None:
    if expected is OK:
        Heartbeat(**given)
    else:
        with pytest.raises(AssertionError):
            Heartbeat(**given)


@pytest.mark.parametrize('init, expected', [
    (dict(fastest=1, slowest=8), [4.5, 2.25, 1.125, 1.0, 1.0]),
    (dict(fastest=2, slowest=8), [5.0, 2.50, 2.000, 2.0, 2.0]),
    (dict(fastest=1, slowest=9), [5.0, 2.50, 1.250, 1.0, 1.0]),
    (dict(fastest=1.5, slowest=9, start=8), [8, 4, 2, 1.5, 1.5]),
])
def test_faster(init: dict, expected: list[float]) -> None:
    hb = Heartbeat(**init)
    delays = []
    for _ in range(5):
        delays.append(hb.delay)
        hb.faster()
    assert delays == expected


@pytest.mark.parametrize('init, expected', [
    (dict(fastest=2, slowest=8), [5, 8, 8, 8, 8]),
    (dict(fastest=2, slowest=30, start=4), [4, 8, 16, 30, 30]),
])
def test_slower(init: dict, expected: list[float]) -> None:
    hb = Heartbeat(**init)
    delays = []
    for _ in range(5):
        delays.append(hb.delay)
        hb.slower()
    assert delays == expected


def test_delay():
    hb = Heartbeat(fastest=1, start=13, slowest=120)
    assert hb.delay == 13
    hb.delay = 42
    assert hb.delay == 42


def test_sync_wait():
    hb = Heartbeat(start=.01)
    it = iter(hb)
    with duration_between(0, .001):
        next(it)
    for _ in range(3):
        with duration_between(.01, .011):
            next(it)

    hb.slower()
    for _ in range(3):
        with duration_between(.02, .021):
            next(it)

    hb.faster()
    for _ in range(3):
        with duration_between(.01, .011):
            next(it)


async def test_async_wait():
    hb = Heartbeat(start=.01)
    it = hb.__aiter__()
    with duration_between(0, .001):
        await it.__anext__()
    for _ in range(3):
        with duration_between(.01, .011):
            await it.__anext__()

    hb.slower()
    for _ in range(3):
        with duration_between(.02, .021):
            await it.__anext__()

    hb.faster()
    for _ in range(3):
        with duration_between(.01, .011):
            await it.__anext__()


async def test_async_loop():
    hb = Heartbeat(start=.01)
    with duration_between(.01, .011):
        i = 0
        async for _ in hb:
            i += 1
            if i == 2:
                break
