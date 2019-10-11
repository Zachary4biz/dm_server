# encoding:utf-8
# author: zac
# create-time: 2019-08-23 16:00
# usage: -
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import os
os.environ['GLOG_minloglevel'] = '2'
from config import CONFIG_NEW
from util.logger import Logger
from util import common_util
from util.cv_util import CVUtil
import itertools
from .yolo import YOLOModel
from django.conf import settings
from urllib.parse import unquote

NAME = "obj"
cvUtil = CVUtil()
TIMEOUT = CONFIG_NEW[NAME].timeout
logger = settings.LOGGER[NAME]
modelClassifier = settings.ALGO_MODEL[NAME]


def _predict(img):
    try:
        res = []
        objs_found = modelClassifier.detect_image_noshow(img)
        for k, g in itertools.groupby(sorted(objs_found)):
            res.append({"obj": k, "cnt": len(list(g))})
        return res, "success"
    except Exception as e:
        logger.error(e)
        return None, repr(e.message)


def get_default_res(info="default res"):
    return []


from django.http import HttpResponse

param_check_list = ['img_url', 'id']


def predict(request):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])
        img, delta_t = common_util.timeit(cvUtil.img_from_url_PIL, img_url)
        logger.debug("[finished] cvutil loading image after {:.4f}".format(delta_t))
        if img is None:
            logger.error("at [id]: {} load img fail from [ur]: {}".format(params['id'], img_url))
            json_str = json.dumps({"result": get_default_res(info='load img fail')})
        else:
            res, remark = _predict(img)
            if res is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
            else:
                json_str = json.dumps({"result": res})
        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")
        if total_delta > TIMEOUT * 1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")

        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)

# logger.info(">>>> init finished") # 可以打开注释，用来检验django服务是否有重启？是否有多次初始化
