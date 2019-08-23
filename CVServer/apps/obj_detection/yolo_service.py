# encoding:utf-8
# author: zac
# create-time: 2019-08-23 16:00
# usage: - 
import json
import time
from ...util.logger import Logger
from ...util import config
from ...util import common_util
from ...util.cv_util import CVUtil
import itertools

logger = Logger('yolo_service', log2console=False, log2file=True, logfile=config.YOLO_LOG_PATH).get_logger()

#########
# cv part
#########
import sys
import os

os.environ['GLOG_minloglevel'] = '2'
import numpy as np
import cv2
import urllib
from PIL import Image
from yolo import YOLO

print("文件路径:", os.path.dirname(__file__))
basePath = os.path.dirname(__file__)
cvUtil = CVUtil()
params = YOLO._defaults.copy()
params.update({"image": True})
yolo = YOLO(**params)

TIMEOUT = 5
NAME = "nsfw_service"


def _predict(img):
    try:
        res = []
        objs_found = yolo.detect_image_noshow(img)
        for k, g in itertools.groupby(sorted(objs_found)):
            res.append({"obj": k, "cnt": len(list(g))})
        return res, "success"
    except Exception as e:
        logger.error(e)
        return None, repr(e.message)


# TestCase
imgURL = "http://news.cnhubei.com/xw/wuhan/201506/W020150615573270910887.jpg"
image = cvUtil.img_from_url_PIL(imgURL)
pred_res = _predict(image)
print(">>>>>> found classes: {}".format(pred_res))


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
        logger.debug(u"[elapsed-load img]: {} [url]: {}".format(params['img_url'], delta_t))
        if img is None:
            logger.error("at [id]: {} load img fail from [ur]: {}".format(params['id'], params['img_url']))
            json_str = json.dumps({"result": get_default_res(info='load img fail')})
        else:
            res, remark = _predict(img)
            if res is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
            else:
                json_str = json.dumps({"result": res})
        logger.info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed]: {}ms [elapsed-load img]: {}ms".format(params['id'],
                                                                                                params['img_url'],
                                                                                                json_str,
                                                                                                round(
                                                                                                    time.time() - begin,
                                                                                                    5) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)
