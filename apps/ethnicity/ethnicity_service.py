# author: zac
# create-time: 2019-12-18 12:19
# usage: - 
import tensorflow as tf
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
from django.conf import settings
from django.http import HttpResponse
import time
from urllib.parse import unquote
from util import common_util
from ethnicity.ethnicity_model import EthnicityM
import numpy as np

NAME = "ethnicity"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['Indian', 'Negroid', 'Caucasoid', 'Mongoloid']
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
modelClassifier: EthnicityM = settings.ALGO_MODEL[NAME]

param_check_list = ['img_url', 'id']


def _predict(img):
    try:
        face_list, delta_t = common_util.timeit(cvUtil.get_face_list, img)
        logger.debug("[elapsed-dlib face]:{}".format(delta_t))
        if len(face_list) == 0:
            return None, "no frontal-face detected."
        else:
            face_list = [cvUtil.pre_cv2caffe(i) for i in face_list]
            pred_list = modelClassifier.predict_batch(face_list)
            res_list = [{"id": np.argmax(pred), "prob": np.max(pred), "info": output[np.max(pred)]}
                        for pred in pred_list]
            return res_list, "success"
    except Exception as e:
        logger.error(e)
        return None, repr(e)


def get_default_res(info="default res"):
    return [{'id': -1, 'prob': 1.0, 'info': info}]


def predict(request):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])  # 图片地址里有参数，转义掉
        img, delta_t = common_util.timeit(cvUtil.img_from_url_cv2, img_url)
        logger.debug("[elapsed-load img]: {} [url]: {}".format(img_url, delta_t))
        if img is None:
            # 图片加载失败
            json_str = json.dumps({"result": get_default_res(info="load img fail")})
            logger.error("at [id]: {} load img fail [ur]: {}".format(params['id'], img_url))
        else:
            # 图片加载完毕
            (res_list, remark) = _predict(img)
            if res_list is None:
                # predict失败
                json_str = json.dumps({"result": get_default_res(info=remark)})
                logger.warn("at [id]: {} [res]: {} [remark]: {}".format(params['id'], json_str, remark))
            else:
                # 正常返回
                json_str = json.dumps({"result": res_list})
                logger.info("at [id]: {} [res]: {}".format(params['id'], json_str))
        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")
        if total_delta > TIMEOUT * 1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")

        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)


