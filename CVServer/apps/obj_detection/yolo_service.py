# encoding:utf-8
# author: zac
# create-time: 2019-08-23 16:00
# usage: -
import os
import sys
sys.path.append(os.path.dirname(__file__)+"/../../")
import json
import time
from util.logger import Logger
from util import config
from util import common_util
from util.cv_util import CVUtil
import itertools

logger = None


def get_logger():
    global logger
    if logger is None:
        logger = Logger('yolo_service', log2console=False, log2file=True, logfile=config.YOLO_LOG_PATH).get_logger()
    return logger


#########
# cv part
#########
import os
os.environ['GLOG_minloglevel'] = '2'
from .yolo import YOLOModel


basePath = os.path.dirname(__file__)
cvUtil = CVUtil()
yolo = None


def get_clf():
    global yolo
    if yolo is None:
        params = YOLOModel._defaults.copy()
        params.update({"image": True})
        ##################################################################
        # 检测模型等配置文件是否存在
        # 实际上这里在django nohup启动时仍然无效，因为这里还是在子线程抛出的异常
        ##################################################################
        for k, v in params.items():
            if k in ["model_path", "anchors_path", "classes_path"]:
                assert os.path.exists(v), "no model-file found: {}".format(v)
        yolo = YOLOModel(**params)
    return yolo


TIMEOUT = 5
NAME = "yolo"


def _predict(img):
    try:
        res = []
        objs_found = get_clf().detect_image_noshow(img)
        for k, g in itertools.groupby(sorted(objs_found)):
            res.append({"obj": k, "cnt": len(list(g))})
        return res, "success"
    except Exception as e:
        get_logger().error(e)
        return None, repr(e.message)


# TestCase
# imgURL = "http://news.cnhubei.com/xw/wuhan/201506/W020150615573270910887.jpg"
# image = cvUtil.img_from_url_PIL(imgURL)
# get_logger().info(">>>>>> img load")
# pred_res = _predict(image)
# get_logger().info(">>>>>> found classes: {}".format(pred_res))


def get_default_res(info="default res"):
    return []


#################
# Django API part
#################
from django.http import HttpResponse

param_check_list = ['img_url', 'id']


def predict(request):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img, delta_t = common_util.timeit(cvUtil.img_from_url_PIL, params['img_url'])
        get_logger().debug("[finished] cvutil loading image after {:.4f}".format(delta_t))
        if img is None:
            get_logger().error("at [id]: {} load img fail from [ur]: {}".format(params['id'], params['img_url']))
            json_str = json.dumps({"result": get_default_res(info='load img fail')})
        else:
            res, remark = _predict(img)
            if res is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
            else:
                json_str = json.dumps({"result": res})
        get_logger().info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed]: {}ms [elapsed-load img]: {}ms".format(params['id'],
                                                                                                params['img_url'],
                                                                                                json_str,
                                                                                                round(
                                                                                                    time.time() - begin,
                                                                                                    5) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)

get_logger().info(">>>> init finished")
