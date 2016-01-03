import time

__author__ = 'peng'

class Message:
    def __init__(self, message, _from):
        self.message = message
        self.time = time.time()
        self._from = _from
