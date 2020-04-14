# encoding=utf-8

##########
# prepare
##########
import time
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import CONFIG_NEW  # config的依赖路径在cofnig.py里已经默认添加
from util.cv_util import CVUtil
from util.tupu import TupuReq
from django.conf import settings
from services import api_format_predict
from urllib.parse import quote, unquote, urlparse, urlencode
from multiprocessing import Pool
import traceback
import json
import numpy as np
import requests
from django.http import HttpResponse
from django.http import HttpRequest
from nsfw import nsfw_service
from nsfw.nsfw_obj import nsfw_obj_service
from nsfw.nsfw_bcnn import nsfw_bcnn_service

NAME = "nonage"
TIMEOUT = CONFIG_NEW[NAME].timeout
tupuReq = TupuReq()
logger = settings.LOGGER[NAME]
param_check_list = ['img_url', 'id']
HOST = os.environ.get("SERVICE_HOST")


def get_default_res(info="default res"):
    return {'nonage': -1, 'rate':1.0, 'info': info}


def predict(request):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])
        id_ = params['id']
        # 请求第三方服务
        child_lbl,lbl_rate,state=tupuReq.request_vulgar(img_url)
        if state == "success":
            # label: 7 未成年
            if child_lbl == 7:
                res_dict={'rate': lbl_rate, 'info': 'nonage'}
            # label: 4 挑逗性行为
            elif child_lbl == 4:
                res_dict={'rate': 0.0, 'info': 'others'}
            else:
                res_dict={'rate': 0.0, 'info': 'others'}
        else:
            res_dict=get_default_res(state)
        json_str = json.dumps({"result":res_dict})
        # log & 超时检测
        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms")
        if total_delta > TIMEOUT*1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms")
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)

