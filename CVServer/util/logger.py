#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Author  : Joshua
@Time    : 2018/10/12 18:48
@File    : logger.py
@Desc    : log
"""

import logging.handlers
import sys
import datetime
import os
from os.path import dirname


DEFAULT_LOGGING_LEVEL = logging.INFO
#DEFAULT_LOGGING_LEVEL = logging.DEBUG


class Logger(object):
    """Log wrapper class
    """

    def __init__(self, loggername,
                 loglevel2console=DEFAULT_LOGGING_LEVEL,
                 loglevel2file=DEFAULT_LOGGING_LEVEL,
                 log2console=True, log2file=False, logfile=None,formatstr=None):
        """Logger initialization
        Args:
            loggername: Logger name, the same name gets the same logger instance
            loglevel2console: Console log level,default logging.DEBUG
            loglevel2file: File log level,default logging.INFO
            log2console: Output log to console,default True
            log2file: Output log to file,default False
            logfile: filename of logfile
        Returns:
            logger
        """

        # create logger
        self.logger = logging.getLogger(loggername)
        self.logger.setLevel(logging.DEBUG)

        # set formater
        logging.Formatter.converter = self.beijing_time
        formatstr = '|%(asctime)s| [%(levelname)s] [%(filename)s-%(lineno)d] %(message)s' if formatstr is None else formatstr
        formatter = logging.Formatter(formatstr, "%Y-%m-%d %H:%M:%S")

        if log2console:
            # Create a handler for output to the console
            ch = logging.StreamHandler(sys.stderr)
            ch.setLevel(loglevel2console)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        if log2file:
            # Create a handler for writing to the log file
            # fh = logging.FileHandler(logfile)
            # Create a handler for changing the log file once a day, up to 15, scroll delete
            fh = logging.handlers.TimedRotatingFileHandler(logfile, when='D', interval=1, backupCount=15, encoding='utf-8')
            fh.setLevel(loglevel2file)
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)

    def get_logger(self):
        return self.logger

    @staticmethod
    def beijing_time(*args, **kwargs):
        beijing_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        return beijing_time.timetuple()
