# ❤️ cardaio

A Python library for adjustable delays.

The main use case is when you want to periodically pull something from a third-party system but you don't know exactly how often the system will have updates. For example, you're monitoring a news website for a particular topic and you want to pull news as soon as they are available but at the same time you don't want to send too many requests when there are no updates.

## 😎 Features

+ 🐍 Pure Python.
+ 🐎 asyncio-first with synchronous API available.
+ 🛡 Fully type-annotated and type-safe.
+ 🪶 Zero-dependency.
+ 🔧 Highly configurable.
+ ☑️ 100% test coverage.

## 📦 Installation

```bash
python3 -m pip install cardaio
```

## 🛠️ Usage

```python
from cardaio import Heartbeat

async def run() -> None:
    hb = Heartbeat(
        # never pull more often than every 1s.
        fastest=1,
        # never pull less often than every 1m.
        slowest=60,
        # start with 10s between iterations.
        start=10,
    )
    async for _ in hb:
        # Pull messages from a remote system.
        msgs = await pull_messages()
        # If there are more than 5 messages,
        # start pulling more often.
        if msgs > 5:
            hb.faster()
        # If there are no messages,
        # pull less often
        elif not msgs:
            hb.slower()
        ...  # do something with messages
```

## 🖨 Acknowledgments

The project is inspired by [cardio.go](https://github.com/Xe/x/blob/master/cardio/cardio.go) Go script introduced by [Xe Iaso](https://xeiaso.net/) in the [Anything can be a message queue if you use it wrongly enough](https://xeiaso.net/blog/anything-message-queue) blog post. The implementation and API are different, though, to make it pythonic and user-friendly.
