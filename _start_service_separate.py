# author: zac
# create-time: 2019-09-12 17:37
# usage: - 
import os
import sys

sys.path.append(os.path.join(os.path.abspath("."), "CVServer"))
import subprocess
import datetime
from zac_pyutils import ExqUtils
from config import *

if sys.argv[1] == "-h" or sys.argv[1] == "--help":
    print("--service 指定开启哪个服务，默认为all")
    print("--host 指定ip")

args_dict = ExqUtils.parse_argv(sys.argv)
SERVICE = args_dict['service']
HOST = args_dict['host']


def start_service(serv_name):
    PORT = CONFIG[serv_name]['port']
    LOGFILE = CONFIG[serv_name]['host_logfile']
    now = datetime.datetime.strftime(datetime.datetime.today(), "%Y-%m-%d_%H:%M:%S")

    if os.path.exists(os.path.dirname(LOGFILE)):
        if os.path.exists(LOGFILE):
            status, output = subprocess.getstatusoutput(r"\cp {} {}".format(LOGFILE, LOGFILE + "." + now))
            print("上次的日志文件cp加上日期时间后缀（精确到秒）. opt-status: {}".format(status))
    else:
        print("日志目录不存在，新建: {}".format(os.path.dirname(LOGFILE)))
        os.mkdir(os.path.dirname(LOGFILE))

    os.environ.setdefault("SERVICE_NAME", serv_name)
    os.environ.setdefault("SERVICE_HOST", str(HOST))
    os.environ.setdefault("SERVICE_PORT", str(PORT))
    status, output = subprocess.getstatusoutput('nohup python -u manage_cutcut_server.py runserver {}:{} > {} 2>&1 &'.format(HOST, PORT, LOGFILE))
    print(">>> 启动服务 {} 于 {}:{} ".format(serv_name, HOST, PORT))
    print(">>> {}: subprocess status is: {}, output is: {}".format("SUCCESS" if status == 0 else "FAIL", status, output))


if SERVICE == "all":
    print("分别启动所有服务")
    assert False, "使用starts.sh里循环bash启动所有 | 不支持一个py内部起多个django服务，会导致environ冲突（属于同一个py进程，共用environ）"
    for i in CONFIG.keys():
        start_service(i)
else:
    start_service(SERVICE)

# nohup python -u manage_cutcut_server.py runserver ${localIP}:8000 > ${logfile}  2>&1 &
