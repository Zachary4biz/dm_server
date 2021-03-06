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
import time
import datetime
import os
from os.path import dirname
from pytz import timezone
from kafka import KafkaProducer

DEFAULT_LOGGING_LEVEL = logging.INFO


# DEFAULT_LOGGING_LEVEL = logging.DEBUG


class KafkaLoggingHandler(logging.Handler):
    BOOTSTRAP='datanode001.eq-sg-2.apus.com:9092,datanode002.eq-sg-2.apus.com:9092,datanode003.eq-sg-2.apus.com:9092,datanode004.eq-sg-2.apus.com:9092,datanode005.eq-sg-2.apus.com:9092,datanode006.eq-sg-2.apus.com:9092,datanode007.eq-sg-2.apus.com:9092,datanode008.eq-sg-2.apus.com:9092,datanode009.eq-sg-2.apus.com:9092,datanode010.eq-sg-2.apus.com:9092'
    # TUPU_TOPIC="apus.three.call.log.tupu.nonage"
    # NETEASE_TOPIC="apus.three.call.log.netease.nsfw"
    def __init__(self,topic):
        logging.Handler.__init__(self)
        # kafka producer
        self.producer = KafkaProducer(bootstrap_servers=self.BOOTSTRAP)
        self.topic = topic
        logging.Formatter.converter = Logger.beijing
        formatstr = '|%(asctime)s| [%(thread)d] [%(levelname)s] [%(filename)s-%(lineno)d] %(message)s'
        formatter = logging.Formatter(formatstr, "%Y-%m-%d %H:%M:%S")
        self.setFormatter(formatter)

    def emit(self, record):
        #drop kafka logging to avoid infinite recursion
        if record.name == 'kafka':
            return
        try:
            #use default formatting
            msg = self.format(record)
            self.producer.send(self.topic, bytearray(msg,'utf-8'))
        except:
            import traceback
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei

    def close(self):
        logging.Handler.close(self)


class Logger(object):
    """Log wrapper class
    """

    def __init__(self, loggername,
                 loglevel2console=DEFAULT_LOGGING_LEVEL,
                 loglevel2file=DEFAULT_LOGGING_LEVEL,
                 log2console=True, log2file=False, logfile=None, logfile_err="auto", kafka_topic=None, formatstr=None):
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
        logging.Formatter.converter = self.beijing
        formatstr = '|%(asctime)s| [%(thread)d] [%(levelname)s] [%(filename)s-%(lineno)d] %(message)s' if formatstr is None else formatstr
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
            fh_defualt = logging.handlers.TimedRotatingFileHandler(logfile, when='D', interval=1, backupCount=15,
                                                                   encoding='utf-8')
            fh_defualt.setLevel(loglevel2file)
            fh_defualt.setFormatter(formatter)
            if logfile_err is not None:
                if logfile_err == "auto":
                    logfile_err = os.path.splitext(logfile)[0]+"_error"+os.path.splitext(logfile)[1]
                # 1. 传err文件时，普通的handler只处理INFO级别
                info_filter = logging.Filter()
                info_filter.filter = lambda record: record.levelno < logging.WARNING  # 设置过滤等级
                fh_defualt.addFilter(info_filter)
                # 2. 新增一个专门处理 WARN和ERROR的handler
                err_filter = logging.Filter()
                err_filter.filter = lambda record: record.levelno >= logging.WARNING
                fh_err = logging.handlers.TimedRotatingFileHandler(logfile_err, when='D', interval=1, backupCount=15,
                                                                   encoding='utf-8')
                fh_err.setLevel(loglevel2file)
                fh_err.setFormatter(formatter)
                fh_err.addFilter(err_filter)
                self.logger.addHandler(fh_err)
            self.logger.addHandler(fh_defualt)
        if kafka_topic is not None:
            self.logger.addHandler(KafkaLoggingHandler(kafka_topic))

    def get_logger(self):
        return self.logger

    @staticmethod
    def beijing(sec, what):
        beijing_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8))
        return beijing_time.timetuple()


if __name__ == '__main__':
    # logger = Logger('cutcut_profile', log2console=False, log2file=True, logfile="abcd.log").get_logger()
    # logger = Logger('cutcut_profile', log2console=False, log2file=True, logfile="abcd.log",
    #                 logfile_err="abcd_err.log").get_logger()
    logger = Logger('cc',log2console=True,log2file=False,kafka_topic="apus.three.call.log.netease.nsfw").get_logger()
    # logger.addHandler(KafkaLoggingHandler("apus.three.call.log.netease.nsfw"))
    logger.debug("a debug")
    logger.info("an info")
    logger.error("an error")
