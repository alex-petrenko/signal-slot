# signal-slot

[![tests](https://github.com/alex-petrenko/signal-slot/actions/workflows/test-ci.yml/badge.svg)](https://github.com/alex-petrenko/signal-slot/actions/workflows/test-ci.yml)
[![Downloads](https://pepy.tech/badge/signal-slot-mp)](https://pepy.tech/project/signal-slot-mp)
[<img src="https://img.shields.io/discord/987232982798598164?label=discord">](https://discord.gg/BCfHWaSMkr)

Qt-like event loops, signals and slots for communication across threads and processes in Python.

### Recent releases

##### v1.0.1
* Added signal_slot.configure_logger() function to configure a custom logger

##### v1.0.0
* First PyPI version

### Installation

```bash
pip install signal-slot-mp
```

### Contributing

Local installation for development:

```bash
pip install -e .[dev]
```

Automatic code formatting:

```bash
make format && make check-codestyle
```

Run tests:

```bash
make test
```

Documentation contributions are welcome.

### Footnote

Originally designed for Sample Factory 2.0, a high-throughput asynchronous RL codebase https://github.com/alex-petrenko/sample-factory.
Distributed under MIT License (see LICENSE), feel free to use for any purpose, commercial or not, at your own risk.

See also https://github.com/Numergy/signalslot