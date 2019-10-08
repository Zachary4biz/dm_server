# author: zac
# create-time: 2019-10-08 11:17
# usage: -

import os
import sys
sys.path.append(os.path.join(os.path.abspath("."), "CVServer"))
from config import CONFIG_NEW

SERVICE = os.environ['SERVICE_NAME']
HOST = os.environ['SERVICE_HOST']
PORT = os.environ['SERVICE_PORT']

bind = "{}:{}".format(HOST, PORT)
worker = 4  # 核心数
errorlog = CONFIG_NEW[SERVICE].gunicorn_logfile+".err"
accesslog = CONFIG_NEW[SERVICE].gunicorn_logfile
proc_name = "gunicorn_server"
