"""
This module contains all messaging related classes
"""

import json
import time

from PyQt5.QtCore import pyqtSignal, QThread
from domain.model import Measurement


class MessageConsumerBase(QThread):
    LOG_TAG = "[MessageConsumerBase] "
    SIGNAL_NEW_MEASUREMENT = pyqtSignal(Measurement)

    def __init__(self):
        super().__init__()
        self._interrupted = False

    def interrupt(self):
        self._interrupted = True

    def _try_parse_measurements_from_line(self, line):
        """Tries to parse a received line from a stream. Returns Measurements, if succeeded. Empty list otherwise."""
        # decode
        try:
            if not isinstance(line, str):
                line = str(line, "utf-8")
        except Exception as e:
            print(self.LOG_TAG + "could not convert line to utf-8: %s" % (str(e), ))
            return []

        if line.startswith("{") and line.strip().endswith("}") and line.count("measurements") == 1:
            # measurement line
            try:
                data = json.loads(line)
                print(data)
            except:
                print(self.LOG_TAG + "Failed to parse json: %s" % (line, ))
                return []

            if "measurements" not in data:
                return []

            measurements = [Measurement(m_data["angle"], m_data["distance"]) for m_data in data["measurements"]]
            return measurements
        return []

    def run(self):
        raise NotImplemented()


class StreamMessageConsumer(MessageConsumerBase):
    """
    Consumer, that reads data from a file or stream-like object and emits the new measurement signal.
    """
    def __init__(self, input_stream, delay=0):
        """
        :param input_stream: the input stream-like object to read input json data from
        :param delay: if >0, the delay in seconds between two emitted signals
        """
        super().__init__()
        self.input_stream = input_stream
        self.delay = delay

    def run(self):
        """
        Reads from (a potentially endless) stream and emits the SIGNAL_NEW_MEASUREMENT signal for every successfully
        parsed measurement.
        """
        with self.input_stream as data:
            while not self._interrupted:
                line = data.readline()
                if not line:
                    time.sleep(0.2)
                    continue
                measurements = self._try_parse_measurements_from_line(line)
                for measurement in measurements:
                    self.SIGNAL_NEW_MEASUREMENT.emit(measurement)
                    if self.delay > 0:
                        time.sleep(self.delay)