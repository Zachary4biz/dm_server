# author: zac
# create-time: 2019-09-16 11:47
# usage: - 
import os
import sys
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), "../../")))
service_name = sys.argv[1]
os.environ.setdefault("SERVICE_NAME", str(service_name))
from config import CONFIG_NEW


def kill_service(service_name_inp):
    port = CONFIG_NEW[service_name_inp].port
    print("    -将kill服务:{} at port:{}".format(service_name_inp, port))
    status, output = subprocess.getstatusoutput(r"ps -ef | grep ':{}' | grep -v 'grep'".format(port))
    if status != 0:
        print("    [ERROR] grep操作失败: [service]:{} [port]:{} [status]:{} [output]:{}".format(service_name_inp, port, status, output))
        return
    res = []
    for line in output.split("\n"):
        params = [i for i in line.split(" ") if i != ""]
        pid = params[1]
        print(f"    kill pid: {pid}")
        status, output = subprocess.getstatusoutput("kill -9 {}".format(pid))
        res.append([status, pid, output])

    for j in res:
        if j[0] != 0:
            print(j)


if service_name in ["all", "seq"]:
    for i in CONFIG_NEW.keys():
        kill_service(i)
else:
    kill_service(service_name)
