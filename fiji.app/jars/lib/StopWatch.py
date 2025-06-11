from ij import IJ
import datetime

class StopWatch(object):
    _shared_instance = None

    def __new__(cls):
        if cls._shared_instance is None:
            cls._shared_instance = super(StopWatch, cls).__new__(cls)
            cls._shared_instance._start_time = None
        return cls._shared_instance

    def start(self, message=""):
        if self._start_time is not None:
            IJ.log("StopWatch already running")
        self._start_time = datetime.datetime.now()
        if message:
            IJ.log(message)

    def stop(self, message=""):
        if self._start_time is None:
            IJ.log("StopWatch has not been started")
            return
        end_time = datetime.datetime.now()
        duration = end_time - self._start_time
        milliseconds = int(duration.total_seconds() * 1000.0)
        IJ.log(message + " finished in: " + str(milliseconds) + " milliseconds")
        self._start_time = None  # reset

# Gebruik het gewoon als:
#StopWatch().start("Loading data...")
# ...do something useful ...
#StopWatch().stop("Loading data")
