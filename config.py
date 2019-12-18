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
import sys
sys.path.append(os.path.dirname(__file__))
from apps.util.cv_util import CVUtil
from apps.util.logger import Logger
cvUtil = CVUtil()
BaseDir = os.path.dirname(__file__)
BaseLogDir = os.path.dirname(os.path.abspath(__file__))+"/logs"
if not os.path.exists(BaseLogDir):
    os.mkdir(BaseLogDir)


# 每个服务的参数
class Params:
    def __init__(self, port, service_name, timeout=6, worker_num=2, use_lazy=False):
        # gunicorn启动server时（_start_service...）里会用到的参数
        self.host_logfile = BaseLogDir + f"/localhost_{service_name}.log"
        self.gunicorn_logfile = BaseLogDir + f"/gunicorn_{service_name}.log"
        self.worker_num = worker_num
        # profile及各子服务自身的参数
        self.port = port
        self.timeout = timeout
        self.service_logfile = BaseLogDir + f"/{service_name}"+f"/{service_name}_service.log"
        if not os.path.exists(BaseLogDir + f"/{service_name}"):
            os.mkdir(BaseLogDir + f"/{service_name}")
        # 是否使用懒加载初始化各个子服务？一般都不考虑使用懒加载，避免加载过程中来的请求全都超时了
        self.use_lazy = use_lazy
        self.logger = Logger(loggername=service_name, log2console=False, log2file=True, logfile=self.service_logfile).get_logger()

    def load_model(self):
        pass


class AgeParams(Params):
    def load_model(self):
        print(">>> init age model. [pid]:{} [ppid]:{}".format(os.getpid(), os.getppid()))
        return cvUtil.load_model(prototxt_fp=os.path.join(BaseDir, "apps/age/model/full_age.prototxt"),
                                 caffemodel_fp=os.path.join(BaseDir, "apps/age/model/full_age.caffemodel"))


class GenderParams(Params):
    def load_model(self):
        return cvUtil.load_model(prototxt_fp=os.path.join(BaseDir, "apps/gender/model/gender_deploy_correct.prototxt"),
                                 caffemodel_fp=os.path.join(BaseDir, "apps/gender/model/gender_model_correct.caffemodel"))


class NSFWParams(Params):
    def load_model(self):
        return cvUtil.load_model(prototxt_fp=os.path.join(BaseDir, "apps/nsfw/model/nsfw_deploy.prototxt"),
                                 caffemodel_fp=os.path.join(BaseDir, "apps/nsfw/model/resnet_50_1by2_nsfw.caffemodel"))


class ObjParams(Params):
    def load_model(self):
        from apps.obj_detection.yolo import YOLOModel
        print(">>> loading clf (should be init) at [pid]: {} [ppid]: {}".format(os.getpid(), os.getppid()))
        params = YOLOModel._defaults.copy()
        params.update({"image": True})
        for k, v in params.items():
            if k in ["model_path", "anchors_path", "classes_path"]:
                assert os.path.exists(v), "no model-file found: {}".format(v)
        return YOLOModel(**params)


class EthnicityParams(Params):
    def load_model(self):
        from apps.ethnicity.ethnicity_model import EthnicityM
        return EthnicityM()

# 每个服务的参数
if os.environ['SERVICE_NAME'] == "all":
    assert False, "service_name as 'all' should have been already forbidden in .sh"
    # CONFIG_NEW = {
    #     'age': AgeParams(port=8001, service_name="age", timeout=10, worker_num=2),
    #     'gender': GenderParams(port=8001, service_name="gender", timeout=10, worker_num=2),
    #     'nsfw': NSFWParams(port=8001, service_name="nsfw", timeout=10, worker_num=4),
    #     'obj': ObjParams(port=8001, service_name="obj", timeout=10, worker_num=3),
    #     'cutcut_profile': Params(port=8000, service_name="cutcut_profile"),
    #     'all': Params(port=8001, service_name="all"),
    # }
else:
    CONFIG_NEW = {
        'age': AgeParams(port=8001, service_name="age", timeout=10, worker_num=4),
        'gender': GenderParams(port=8002, service_name="gender", timeout=10, worker_num=4),
        'nsfw': NSFWParams(port=8003, service_name="nsfw", timeout=10, worker_num=4),
        'obj': ObjParams(port=8004, service_name="obj", timeout=10, worker_num=4),
        'vectorize': Params(port=8005, service_name="vectorize", timeout=5, worker_num=2),
        'ethnicity': Params(port=8006, service_name="ethnicity", timeout=5, worker_num=2),
        'cutcut_profile': Params(port=8000, service_name="cutcut_profile", worker_num=3),
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
                if i == "load_model":
                    print("  ", CONFIG_NEW[k].load_model())
