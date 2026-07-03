# asyncio-channel

[![CI](https://github.com/ebb29c/asyncio-channel/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ebb29c/asyncio-channel/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ebb29c/asyncio-channel/branch/main/graph/badge.svg)](https://codecov.io/gh/ebb29c/asyncio-channel)

Asynchronous channels for communication and synchronization between `asyncio` coroutines.

```python
from asyncio_channel import create_channel

# Create a new channel.
ch = create_channel()

# Put an item on the channel; block until the item is accepted.
await ch.put(x)

# Take an item from the channel; block until an item is available.
x = await ch.take()

# Do something each time an item is put on the channel.
async for x in ch:
	do_something(x)
	do_something_else(x)
# Iteration stops when the channel is closed and drained.
```

Also contains several utilities for piping items between channels, mixing multiple input channels, routing messages by topic, and more.

## API Documentation

See the full [API docs](docs/api.md)

## Install

From [pypi](https://pypi.org/project/asyncio-channel)

```sh
$ pip install asyncio-channel
```

Requires Python 3.11 or newer.

## Setup for development

*Tip*: Use [pyenv](https://github.com/pyenv/pyenv) to manage Python versions.

```sh
$ git clone https://github.com/ebb29c/asyncio-channel.git
$ cd asyncio-channel
$ python3 -m venv .venv
$ . .venv/bin/activate
$ make install
$ make test
```

Other `make` targets:
- `test-cov`: run tests with code coverage
- `test-cov-html`: run tests and generate html code coverage report
- `test-cov-xml`: run tests and generate xml code coverage report
- `lint`: run linter
- `lint-fix`: run linter and apply fixes
- `format`: format the code
- `typecheck`: run mypy

## Releasing

See [docs/releasing.md](docs/releasing.md); pushing a version tag runs the
automated release pipeline.

## License

[The MIT License](LICENSE)
