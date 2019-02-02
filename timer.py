import logging, threading, functools, time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class PeriodicTimer(threading.Thread):
    def __init__(self, interval, function, args=None, kwargs=None):
        threading.Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = threading.Event()
        self.daemon = True

    def cancel(self):
        """Stop the timer if it hasn't finished yet."""
        self.finished.set()

    def run(self):
        next_call = time.time() + self.interval
        should_cancel = False
        self.finished.wait(self.interval)

        while not self.finished.is_set() and not should_cancel:
            should_cancel = self.function(*self.args, **self.kwargs)

            next_call = next_call + self.interval
            to_wait = max(next_call - time.time(), 0)
            self.finished.wait(to_wait)

        self.finished.set()
