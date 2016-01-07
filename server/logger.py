import logging
from singleton import *

__author__ = 'hupeng'


@singleton
class Logger:
    def __init__(self):
        self.logger = logging.getLogger('Chat-Server')
        log_file = logging.FileHandler('Chat-Server.log')
        log_file.setLevel(logging.DEBUG)
        log_stream = logging.StreamHandler()
        log_stream.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
        log_stream.setFormatter(formatter)
        log_file.setFormatter(formatter)
        self.logger.addHandler(log_file)
        self.logger.addHandler(log_stream)

    def info(self, info):
        self.logger.info(info)

    def error(self, error):
        self.logger.error(error)

    def debug(self, info):
        self.logger.debug(info)

    def warn(self, warn):
        self.logger.warn(warn)
