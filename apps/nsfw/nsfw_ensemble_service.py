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

NAME = "nsfw_ensemble"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['normal pic', 'nsfw pic']
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
# modelClassifier = settings.ALGO_MODEL[NAME]
load_img_func = cvUtil.img_from_url_cv2
param_check_list = ['img_url', 'id']
HOST = os.environ.get("SERVICE_HOST")
NSFW_OBJ_NAME="nsfw_obj"
NSFW_BCNN_NAME="nsfw_bcnn"
sub_service_names = [NSFW_OBJ_NAME, NSFW_BCNN_NAME]

from nsfw.nsfw_obj import nsfw_obj_service
from nsfw.nsfw_bcnn import nsfw_bcnn_service
sub_service_default = {
    "nsfw_obj":nsfw_obj_service.get_default_res(),
    "nsfw_bcnn":nsfw_bcnn_service.get_default_res(),
}

def get_default_res(info="default res"):
    return {'nsfw_prob': -1, 'sfw_prob': -1, 'info': info}

# 为了用multiprocessing，需要避免用到module（不能pickle），所以把service用到的属性取出来作为字典
def request_service_http_multiProcess(zipped_param):
    service_info, request_url_inp = zipped_param
    ser_timeout = service_info['TIMEOUT']
    ser_default = service_info['default_res']
    begin = time.time()
    is_success = "success"
    # print(">>> service:{}, request_url:{}".format(service_info['NAME'], request_url_inp))
    try:
        res = requests.get(request_url_inp, timeout=ser_timeout).text
        res = json.loads(res)['result']
    except Exception as e:
        is_success = str(repr(e)) + "\t" + traceback.format_exc()
        res = ser_default
    delta_t = round(time.time() - begin, 5) * 1000
    return res, delta_t, is_success


def predict(request):
    # return api_format_predict(request,
    #                           logger=logger, param_check_list=param_check_list,
    #                           load_img_func=load_img_func, get_default_res=get_default_res, _predict=_predict,
    #                           TIMEOUT=CONFIG_NEW[NAME].timeout)
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])
        id_ = params['id']
        # 拼接子服务的请求url
        request_urls = []
        for name in sub_service_names:
            port=CONFIG_NEW[name].port
            ser_name=CONFIG_NEW[name].service_name
            request_urls.append(f"http://{HOST}:{port}/{ser_name}?img_url={img_url}&id={id_}")
        
        # 拼接一些 request_service_http_multiProcess 必须的参数
        service_info_list=[{
            "NAME":CONFIG_NEW[ser_name].service_name,
            "TIMEOUT":CONFIG_NEW[ser_name].timeout,
            "default_res":sub_service_default[ser_name]} for ser_name in sub_service_names]

        # 并发请求
        p = Pool(2)
        r = p.map(func=request_service_http_multiProcess, iterable=list(zip(service_info_list, request_urls)))
        result = dict(zip([i['NAME'] for i in service_info_list], r))  # 多进程结果顺序和输入服务的顺序一样，zip到一起避免后续取数据的时候出错
        p.close()
        p.join()

        # 鉴黄目前merge策略就是简单的取max
        nsfw_score=-1
        for ser_name, v in result.items():
            res, delta_t, is_success = v
            if is_success != "success":
                # 失败的子服务输出日志
                logger.error("[SERVICE]:{} [id]:{} [ERR]:{} [res]:{}".format(ser_name, id_, is_success.split("\t")[0],res))
                logger.debug(is_success)
                # if ser_name == NSFW_OBJ_NAME:
                #     pass
                # elif ser_name == NSFW_BCNN_NAME:
                #     pass
                # else:
                #     assert False,f"ser_name:{ser_name} not in sub_service_names [{NSFW_OBJ_NAME}, {NSFW_BCNN_NAME}]"
            else:
                logger.info(f"[id]:{id_} [SERVICE]:{ser_name} [delta]: {delta_t} [res]:{res}")
                if ser_name == NSFW_OBJ_NAME:
                    obj_score=max([i['prob'] for i in res]) if len(res)>0 else 0.0
                    if  obj_score > nsfw_score:
                        nsfw_score = obj_score
                elif ser_name == NSFW_BCNN_NAME:
                    bcnn_score=res["nsfw_prob"]
                    if  bcnn_score > nsfw_score:
                        nsfw_score = bcnn_score
                else:
                    assert False,f"ser_name:{ser_name} not in sub_service_names [{NSFW_OBJ_NAME}, {NSFW_BCNN_NAME}]"
        if nsfw_score > -1:
            nsfw_score = round(float(nsfw_score), 4) 
            sfw_score = round(float(1-nsfw_score), 4)
            res=[sfw_score, nsfw_score]
            res_dict={'nsfw_prob': res[1], 'sfw_prob': res[0], 'info': output[np.argmax(res)]}
        else:
            res_dict=get_default_res("both bcnn&yolo failed")
        json_str = json.dumps({"result":res_dict})

        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")
        if total_delta > TIMEOUT*1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")

        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)


