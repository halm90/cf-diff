"""
scaler logger functions.
"""
import logging
import os
import sys

import constants
from singleton import Singleton


class Logger(object, metaclass=Singleton):
    _avail_levels = {'DEBUG': logging.DEBUG,
                     'INFO': logging.INFO,
                     'WARNING': logging.WARNING,
                     'ERROR': logging.ERROR,
                     'CRITICAL': logging.CRITICAL}
    def __init__(self, appname=None, level=None):
        """
        Get a logger object for application-wide use.
        """
        appname = appname or os.environ.get('APPNAME', __name__)
        loglevel = str(level or os.environ.get('LOG_LEVEL',
                                               constants.DEFAULT_LOG_LEVEL)).upper()

        self._logger = logging.getLogger(appname)
        self._logger.addHandler(logging.StreamHandler(sys.stdout))
        self.set_level(loglevel)
        super().__init__()

    def set_level(self, level):
        if level in self._avail_levels:
            self._logger.setLevel(self._avail_levels[level])
        else:
            self.logger.error("Can't set log level to %s", level)

    @property
    def logger(self):
        return self._logger
