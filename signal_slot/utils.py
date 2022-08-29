import logging


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


@static_vars(history=dict())
def log_every_n(logger, n, _level, msg, *args, **kwargs):
    """
    Log message `msg` once in n calls to this function to avoid log spam.
    Use only msg to count the calls, not args and kwargs.
    """
    if msg not in log_every_n.history:
        log_every_n.history[msg] = 0

    num_msgs = log_every_n.history[msg]
    if num_msgs % n == 0:
        msg_with_ntimes = f"{msg} ({num_msgs} times)" if num_msgs > 1 else msg
        logger.log(_level, msg_with_ntimes, *args, **kwargs)

    log_every_n.history[msg] += 1


def debug_log_every_n(logger, n, msg, *args, **kwargs):
    log_every_n(logger, n, logging.DEBUG, msg, *args, **kwargs)


def error_log_every_n(logger, n, msg, *args, **kwargs):
    log_every_n(logger, n, logging.ERROR, msg, *args, **kwargs)
