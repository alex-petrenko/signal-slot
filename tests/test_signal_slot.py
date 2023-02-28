import datetime
import logging
import multiprocessing
import time
from queue import Empty

import pytest

from signal_slot.queue_utils import get_mp_queue
from signal_slot.signal_slot import EventLoop, EventLoopObject, EventLoopProcess, Timer, log, process_name, signal

logging.basicConfig(level=logging.NOTSET)


class C1(EventLoopObject):
    def __init__(self, event_loop, object_id):
        super().__init__(event_loop, object_id)
        self.x = 0

    @signal
    def reply(self):
        pass

    @signal
    def broadcast_signal(self):
        pass

    def inc(self, data):
        self.x += 1
        log.debug(f"inc slot {self.object_id} {self.x=} {data=} process={process_name(self.event_loop.process)}")
        self.reply.emit(process_name(self.event_loop.process), self.x)

    def on_timeout(self):
        log.debug(
            f"on_timeout slot {self.object_id} {self.x=} process={process_name(self.event_loop.process)}, {datetime.datetime.now()}"
        )
        self.broadcast_signal.emit(42, 43)

    def on_bcast(self, arg1, arg2):
        log.info(
            f"on_bcastC1 slot {self.object_id} {arg1=} {arg2=} process={process_name(self.event_loop.process)}, {datetime.datetime.now()}"
        )


class C2(EventLoopObject):
    def __init__(self, event_loop, object_id):
        super().__init__(event_loop, object_id)
        self.pi = 3.14

    @signal
    def foo_signal(self):
        pass

    def foo(self, data):
        log.debug("Foo")
        self.foo_signal.emit(data)

    def on_reply(self, p, x):
        log.debug("reply from %s(%d) received by %s %s", p, x, self.object_id, process_name(self.event_loop.process))

    def on_bcast(self, arg1, arg2):
        log.info(
            f"on_bcastC2 slot {self.object_id} {arg1=} {arg2=} process={process_name(self.event_loop.process)}, {datetime.datetime.now()}"
        )


class C3(EventLoopObject):
    @signal
    def s1(self):
        pass


class C4(EventLoopObject):
    def on_start(self):
        log.debug(f"{self.on_start.__name__} start")

    def on_s1(self, arg1, arg2):
        log.info(f"{self.on_s1.__name__} {arg1=} {arg2=}")


def test_basic():
    # create some objects, connect them, run the event loop
    event_loop = EventLoop("main_loop")

    o1 = C1(event_loop, "o1")
    o2 = C2(event_loop, "o2")

    o2.foo_signal.connect(o1.inc)
    o2.foo_signal.disconnect(o1.inc)
    o2.foo_signal.connect(o1.inc)

    p = EventLoopProcess(unique_process_name="my_process1")
    o3 = C1(p.event_loop, "o3_p")
    o4 = C2(p.event_loop, "o4_p")

    t = Timer(p.event_loop, 2.0)

    o2.foo_signal.connect(o3.inc)
    o4.foo_signal.connect(o3.inc)
    o4.foo_signal.connect(o3.inc)

    p2 = EventLoopProcess(unique_process_name="my_process2")
    o5 = C1(p2.event_loop, "o5_p2")
    o6 = C2(p2.event_loop, "o6_p2")

    o2.foo_signal.connect(o5.inc)
    o6.foo_signal.connect(o5.inc)

    o5.reply.connect(o2.on_reply)
    o5.reply.connect(o4.on_reply)
    o5.reply.connect(o6.on_reply)
    o5.reply.connect(o6.on_reply)

    o6.detach()
    del o6

    o7 = C1(p2.event_loop, "o7_p2")
    o8 = C2(p2.event_loop, "o8_p2")

    o5.reply.connect(o8.on_reply)

    o1.broadcast_signal.broadcast_on(p2.event_loop)

    o7.subscribe("broadcast_signal", o7.on_bcast)
    o8.subscribe("broadcast_signal", o8.on_bcast)

    t.timeout.connect(o7.on_timeout)
    t.timeout.connect(o1.on_timeout)

    stop_timer = Timer(event_loop, 6.1, single_shot=True)
    stop_timer.timeout.connect(event_loop.stop)
    stop_timer.timeout.connect(p.stop)
    stop_timer.timeout.connect(p2.stop)

    p.start()
    p2.start()

    o2.foo(123)

    event_loop.exec()

    p.join()
    p2.join()


def test_multiarg():
    ctx = multiprocessing.get_context("spawn")
    p = EventLoopProcess("_p1", ctx)

    event_loop = EventLoop("multiarg_loop")
    stop_timer = Timer(event_loop, 0.5, single_shot=True)
    stop_timer.timeout.connect(event_loop.stop)

    o1 = C3(p.event_loop, "o1")
    o2 = C4(p.event_loop, "o2")

    p.event_loop.start.connect(o2.on_start)

    o1.s1.connect(o2.on_s1)
    o1.s1.emit(dict(a=1, b=2, c=3), 42)
    o1.s1.emit_many([(dict(a=1, b=2, c=3), 42), (dict(a=11, b=22, c=33), 422)])

    event_loop.terminate.connect(p.stop)

    p.start()
    log.debug(f"Starting event loop {event_loop}")
    event_loop.exec()
    p.join()


def test_same_object_name():
    event_loop = EventLoop("main_loop")

    o1 = C1(event_loop, "o1")
    o2 = C2(event_loop, "o2")

    ctx = multiprocessing.get_context("spawn")
    p = EventLoopProcess("p", ctx)

    o3 = C1(p.event_loop, "o1")
    o4 = C2(p.event_loop, "o2")

    with pytest.raises(Exception) as context:
        o1.reply.connect(o2.on_reply)
        o1.reply.connect(o4.on_reply)

        o2.foo_signal.connect(o3.inc)

    assert context.type == ValueError


def test_queue_full():
    event_loop = EventLoop("test_loop_queue_full")
    emitter = C2(event_loop, "emitter")

    for i in range(5):
        receiver = C1(event_loop, f"receiver{i}")
        emitter.foo_signal.connect(receiver.inc)

    # emitting lots of signals before starting the event loop - this should lead to queue overflow
    # most of these signals are lost because of queue overflow, but we should not crash
    lots_of_data = [42] * 100000
    for i in range(100):
        emitter.foo_signal.emit(lots_of_data)
    for i in range(5000):
        emitter.foo_signal.emit(i)


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


def test_usage_example():
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


def test_queue_get_many():
    q = get_mp_queue()

    q.put(1)
    q.put(2)
    q.put(3)

    msgs = []
    while True:
        try:
            msgs.extend(q.get_many_nowait())
        except Empty:
            break

    assert msgs == [1, 2, 3]
