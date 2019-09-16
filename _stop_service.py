# author: zac
# create-time: 2019-09-16 11:47
# usage: - 
from .CVServer.config import *
import sys
import subprocess

service_name = sys.argv[1]
port = CONFIG[service_name]['port']

proc = subprocess.Popen(['ps','-ef'],stdout=subprocess.PIPE)
status, output = subprocess.getstatusoutput(r"ps -ef | grep ':{}' | grep -v 'grep'".format(port))
if status != 0:
    assert False, "ps -ef grep操作失败"

res = []
for line in output.split("\n"):
    params = [i for i in line.split(" ") if i != ""]
    pid = params[1]
    status, output = subprocess.getstatusoutput("kill -9 {}".format(pid))
    res.append([status, pid, output])

for i in res:
    if i[0] != 0 :
        print(i)

