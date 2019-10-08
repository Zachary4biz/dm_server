# author: zac
# create-time: 2019-09-16 10:40
# usage: -
"""
age: 8001
gender: 8002
nsfw: 8003
obj: 8004
profile: 8000
"""
import os
BaseLogDir = os.path.dirname(os.path.abspath(__file__))+"/logs"
if not os.path.exists(BaseLogDir):
    os.mkdir(BaseLogDir)


# 每个服务的参数
class Params:
    def __init__(self, port, service_name, timeout=6, worker_num=2):
        self.port = port
        self.timeout = timeout
        self.host_logfile = BaseLogDir + f"/localhost_{service_name}.log"
        self.gunicorn_logfile = BaseLogDir + f"/gunicorn_{service_name}.log"
        self.service_logfile = BaseLogDir + f"/{service_name}"+f"/{service_name}_service.log"
        if not os.path.exists(BaseLogDir + f"/{service_name}"):
            os.mkdir(BaseLogDir + f"/{service_name}")
        self.worker_num = worker_num


# 每个服务的参数
CONFIG_NEW = {
    'age': Params(port=9001, service_name="age", timeout=8),
    'gender': Params(port=9002, service_name="gender", timeout=8),
    'nsfw': Params(port=9003, service_name="nsfw", timeout=6),
    'obj': Params(port=9004, service_name="obj", timeout=5),
    'cutcut_profile': Params(port=9000, service_name="cutcut_profile"),
}


# NLP服务的地址
class NLP:
    def __init__(self):
        pass
    tag_port = "http://newsprofile-keywords.internalapus.com/segment/tags.jsp"
    kw_port = "http://newsprofile-keywords.internalapus.com/segment/keywords.jsp"


if __name__ == '__main__':
    print(CONFIG_NEW)
    for k in CONFIG_NEW.keys():
        print(">>> {}".format(k))
        for i in dir(CONFIG_NEW[k]):
            if not i.startswith("_"):
                print("  ", i+"="+str(CONFIG_NEW[k].__getattribute__(i)))
