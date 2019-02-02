import logging, functools, time

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class PeriodicTimer:
    def __init__(self, interval, function, args=None, kwargs=None, sleepfunc=time.sleep):
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.sleepfunc = sleepfunc

    def run(self):
        next_call = time.time() + self.interval
        should_cancel = False

        self.sleepfunc(self.interval)

        while not should_cancel:
            should_cancel = self.function(*self.args, **self.kwargs)

            next_call = next_call + self.interval
            to_wait = max(next_call - time.time(), 0)
            self.sleepfunc(to_wait)

def start_timer(timer):
    timer.run()
