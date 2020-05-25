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
from apps import *
from apps.nsfw import nsfw_bcnn,nsfw_obj
from apps.util import model_util
from apps.util.logger import Logger,KafkaLoggingHandler
BaseDir = os.path.dirname(__file__)
BaseLogDir = os.path.dirname(os.path.abspath(__file__))+"/logs"
TFServingPort=8501
if not os.path.exists(BaseLogDir):
    os.mkdir(BaseLogDir)


# 每个服务的参数
class Params:
    def __init__(self, port, service_name, timeout=10, worker_num=2, use_lazy=False,kafka_topic=None):
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
        if kafka_topic is not None:
            self.logger.addHandler(KafkaLoggingHandler(kafka_topic))
        self.service_name = service_name

    def load_model(self):
        pass


class CaffeModelParams(Params):
    def __init__(self, port, service_name, service_module_dir, timeout=6, worker_num=2, use_lazy=False):
        super(CaffeModelParams, self).__init__(port, service_name, timeout=timeout, worker_num=worker_num, use_lazy=use_lazy)
        self.model_dir = os.path.join(service_module_dir, "model")

    def load_model(self):
        print(">>> 加载后缀为 .prototxt 和 .caffemodel 的模型文件")
        proto_file = [os.path.join(self.model_dir, file) for file in os.listdir(self.model_dir) if file.endswith("prototxt")]
        model_file = [os.path.join(self.model_dir, file) for file in os.listdir(self.model_dir) if file.endswith("caffemodel")]
        info = f"""[proto_file]:{", ".join(proto_file)}\n[model_file]:{", ".join(model_file)}"""
        print(info)
        assert len(proto_file) == 1 and len(model_file) == 1, f"""    目录下必须有且只有一个模型文件，当前如下：\n{info}"""
        pf, mf = proto_file[0], model_file[0]
        return model_util.load_model(prototxt_fp=pf, caffemodel_fp=mf)


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


class ServingModelParams(Params):
    def __init__(self, port, service_name, service_module_dir,
                 tf_serving_port, tf_serving_loglevel, tf_serving_domain="0.0.0.0",
                 timeout=6, worker_num=2, use_lazy=False):
        super(ServingModelParams, self).__init__(port, service_name, timeout=timeout, worker_num=worker_num, use_lazy=use_lazy)
        self.tf_serving_domain = tf_serving_domain
        self.tf_serving_port = tf_serving_port
        self.tf_serving_logfile = BaseLogDir + f"/tf_serving_{self.service_name}.log"
        self.tf_serving_loglevel = tf_serving_loglevel
        self.pb_path = os.path.join((os.path.abspath(service_module_dir)), "model")
        self.serving_url = f"http://{self.tf_serving_domain}:{self.tf_serving_port}/v1/models/{self.service_name}:predict"
        self.service_module_dir = service_module_dir

    # 在 settings.py 中调用此方法初始化模型
    def load_model(self):
        return model_util.TFServingModel(self.serving_url)


# 每个服务的参数
if os.environ.get('SERVICE_NAME', None) == "all":
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
        'age': CaffeModelParams(port=8001, service_name="age", service_module_dir=os.path.dirname(age.__file__), timeout=10, worker_num=5),
        'gender': CaffeModelParams(port=8002, service_name="gender", service_module_dir=os.path.dirname(gender.__file__), timeout=10, worker_num=5),
        'nsfw': CaffeModelParams(port=8003, service_name="nsfw", service_module_dir=os.path.dirname(nsfw.__file__), timeout=10, worker_num=5),
        'obj': ObjParams(port=8004, service_name="obj", timeout=10, worker_num=5),
        'vectorize': ServingModelParams(port=8005, service_name="vectorize",
                                        service_module_dir=os.path.dirname(vectorize.__file__),
                                        tf_serving_port=18052, tf_serving_loglevel=0,
                                        timeout=5, worker_num=2),
        'ethnicity': ServingModelParams(port=8006, service_name="ethnicity",
                                        service_module_dir=os.path.dirname(ethnicity.__file__),
                                        tf_serving_port=18051, tf_serving_loglevel=0,
                                        timeout=10, worker_num=3),
        'nsfw_obj': ServingModelParams(port=8007, service_name="nsfw_obj",
                                        service_module_dir=os.path.dirname(nsfw_obj.__file__),
                                        tf_serving_port=18053, tf_serving_loglevel=0,
                                        timeout=10, worker_num=4),
        'nsfw_bcnn': ServingModelParams(port=8008, service_name="nsfw_bcnn",
                                        service_module_dir=os.path.dirname(nsfw_bcnn.__file__),
                                        tf_serving_port=18054, tf_serving_loglevel=0,
                                        timeout=10, worker_num=4),
        'nsfw_ensemble': Params(port=8009, service_name="nsfw_ensemble",timeout=10,worker_num=2,kafka_topic="apus.three.call.log.netease.nsfw"),
        'nonage': Params(port=8010, service_name="nonage",timeout=10,worker_num=2,kafka_topic="apus.three.call.log.tupu.nonage"),
        'cutcut_profile': Params(port=8000, service_name="cutcut_profile", worker_num=2),
    }
    allP=[v for k,v in CONFIG_NEW.items()]
    assert len(allP) == len(set([p.port for p in allP]))
    tfservingP=[p for p in allP if isinstance(p,ServingModelParams)]
    assert len(tfservingP) == len(set([p.tf_serving_port for p in tfservingP]))
    assert all([k==v.service_name for k,v in CONFIG_NEW.items()])


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
