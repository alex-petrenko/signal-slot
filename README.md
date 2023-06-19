# signal-slot

[![tests](https://github.com/alex-petrenko/signal-slot/actions/workflows/test-ci.yml/badge.svg)](https://github.com/alex-petrenko/signal-slot/actions/workflows/test-ci.yml)
[![Downloads](https://pepy.tech/badge/signal-slot-mp)](https://pepy.tech/project/signal-slot-mp)
[<img src="https://img.shields.io/discord/987232982798598164?label=discord">](https://discord.gg/BCfHWaSMkr)

Qt-like event loops, signals and slots for communication across threads and processes in Python.

### Installation

```bash
pip install signal-slot-mp
```

Linux, macOS, and Windows are supported.

### Overview

`signal-slot` enables a parallel programming paradigm inspired by Qt's signals and slots, but in Python.

The main idea can be summarized as follows:

* Application is a collection of `EventLoop`s. Each `EventLoop` is an infinite loop that occupies a thread or a process.
* Logic of the system is implemented in `EventLoopObject`s that live on `EventLoop`s. Each `EventLoop` can support multiple `EventLoopObject`s.
* `EventLoopObject`s can emit signals. A signal "message" contains a name of the signal
and the payload (arbitrary data).
* Components can also connect to signals emitted by other components by specifying a `slot` function to be called when the signal is received
by the EventLoop.

### Usage example

```python
import time
import datetime
from signal_slot.signal_slot import EventLoop, EventLoopObject, EventLoopProcess, Timer, signal

now = datetime.datetime.now

# classes derived from EventLoopObject define signals and slots (actually any method can be a slot)
class A(EventLoopObject):
    @signal
    def signal_a(self):
        ...

    def on_signal_b(self, msg: str):
        print(f"{now()} {self.object_id} received signal_b: {msg}")
        time.sleep(1)
        self.signal_a.emit("hello from A", 42)

class B(EventLoopObject):
    @signal
    def signal_b(self):
        ...

    def on_signal_a(self, msg: str, other_data: int):
        print(f"{now()} {self.object_id} received signal_a: {msg} {other_data}")
        time.sleep(1)
        self.signal_b.emit("hello from B")

# create main event loop and object of type A
main_event_loop = EventLoop("main_loop")
a = A(main_event_loop, "object: a")

# create a background process with a separate event loop and object b that lives on that event loop
bg_process = EventLoopProcess(unique_process_name="background_process")
b = B(bg_process.event_loop, "object: b")

# connect signals and slots
a.signal_a.connect(b.on_signal_a)
b.signal_b.connect(a.on_signal_b)

# emit signal from a to kick off the communication
a.signal_a.emit("Initial hello from A", 1337)

# create a timer that will stop our system after 10 seconds
stop_timer = Timer(main_event_loop, 10.0, single_shot=True)
stop_timer.start()

# connect the stop method of the event loop to the timeout signal of the timer
stop_timer.timeout.connect(main_event_loop.stop)
stop_timer.timeout.connect(bg_process.stop)  # stops the event loop of the background process

# start the background process
bg_process.start()

# start the main event loop
main_event_loop.exec()

# if we get here, the main event loop has stopped
# wait for the background process to finish
bg_process.join()

print(f"{now()} Done!")
```

The output should roughly look like this:

```bash
2022-11-30 01:51:58.943425 object: b received signal_a: Initial hello from A 1337
2022-11-30 01:51:59.944957 object: a received signal_b: hello from B
2022-11-30 01:52:00.945852 object: b received signal_a: hello from A 42
2022-11-30 01:52:01.947599 object: a received signal_b: hello from B
2022-11-30 01:52:02.949214 object: b received signal_a: hello from A 42
2022-11-30 01:52:03.950762 object: a received signal_b: hello from B
2022-11-30 01:52:04.952419 object: b received signal_a: hello from A 42
2022-11-30 01:52:05.953596 object: a received signal_b: hello from B
2022-11-30 01:52:06.954918 object: b received signal_a: hello from A 42
2022-11-30 01:52:07.956701 object: a received signal_b: hello from B
2022-11-30 01:52:08.957755 object: b received signal_a: hello from A 42
2022-11-30 01:52:09.963144 Done!
```

### Implementation details

* There's not argument validation for signals and slots. If you connect a slot to a signal with a different signature,
it will fail at runtime. This can also be used to your advantage by allowing to propagate arbitrary data as
payload with appropriate runtime checks.
* It is currently impossible to connect a slot to a signal if emitter and receiver objects belong to event loops
already running in different processes (although it should be possible to implement this feature).
Connect signals to slots during system initialization.
* Signal-slot mechanism in the current implementation can't implement a message passing protocol where
only a single copy of the signal is received by the subscribers. Signals are always delivered to all connected slots.
Use a FIFO multiprocessing queue if you want only one receiver to receive the signal.

### Multiprocessing queues

At the core of the signal-slot mechanism are the queues that are used to pass messages between processes.
Python provides a default implementation `multiprocessing.Queue`, which turns out to be rather slow.

By default we use a custom queue implementation written in C++ using POSIX API that is significantly faster:
https://github.com/alex-petrenko/faster-fifo.

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

### Recent releases

##### v1.0.5
* Windows support (do not require POSIX-only faster-fifo on Windows)

##### v1.0.4
* Use updated version of faster-fifo 

##### v1.0.3
* Improved logging

##### v1.0.2
* Catching queue.Full exception to handle situations where receiver event loop process is killed

##### v1.0.1
* Added signal_slot.configure_logger() function to configure a custom logger

##### v1.0.0
* First PyPI version

### Footnote

Originally designed for Sample Factory 2.0, a high-throughput asynchronous RL codebase https://github.com/alex-petrenko/sample-factory.
Distributed under MIT License (see LICENSE), feel free to use for any purpose, commercial or not, at your own risk.