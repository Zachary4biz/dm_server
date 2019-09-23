# author: zac
# create-time: 2019-09-16 11:47
# usage: - 
import os
import sys
import subprocess
sys.path.append(os.path.join(os.path.abspath("."), "CVServer"))
from config import *


def kill_service(service_name_inp):
    port = CONFIG[service_name_inp]['port']
    print("    将kill服务:{} at port:{}".format(service_name_inp, port))
    status, output = subprocess.getstatusoutput(r"ps -ef | grep ':{}' | grep -v 'grep'".format(port))
    if status != 0:
        assert False, "ps -ef grep操作失败: service:{} status:{} output:{}".format(service_name_inp, status, output)

    res = []
    for line in output.split("\n"):
        params = [i for i in line.split(" ") if i != ""]
        pid = params[1]
        status, output = subprocess.getstatusoutput("kill -9 {}".format(pid))
        res.append([status, pid, output])

    for j in res:
        if j[0] != 0:
            print(j)


service_name = sys.argv[1]
if service_name == "all":
    for i in CONFIG.keys():
        kill_service(i)
else:
    kill_service(service_name)
