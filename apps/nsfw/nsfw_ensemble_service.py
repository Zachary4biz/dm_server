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
# from util.tupu import TupuReq as NeteaseReq
from util.netease import NeteaseReq
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

NAME = "nsfw_ensemble"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['normal pic', 'nsfw pic', 'sexy pic']
cvUtil = CVUtil()
neteaseReq = NeteaseReq()
logger = settings.LOGGER[NAME]
param_check_list = ['img_url', 'id']
HOST = os.environ.get("SERVICE_HOST")

NSFW_OBJ=nsfw_obj_service
NSFW_CLF=nsfw_service # nsfw_bcnn_service # bcnn训练的样本太少虽然在验证集表现很好，但是实际业务数据还是很多误判
sub_services = [NSFW_CLF] # [NSFW_OBJ, NSFW_CLF]

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
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])
        id_ = params['id']
        # 请求第三方服务
        porn_lbl,lbl_rate,state=neteaseReq.request_porn(img_url)
        if state == "success":
            # label: 0 是正常图片(第三方服务已经经过映射) | 网易是 0 正常图片 | 图谱是：色情 露点、生殖器官、性行为等
            if porn_lbl == 0:
                res_dict={'nsfw_prob': 1-lbl_rate, 'sfw_prob': lbl_rate, 'info': output[0]}
            # label: 1 or 2 是色情(第三方服务已经经过映射) | 网易是 1 or 2 色情图片 | 图谱是 1 是性感 露肩、露大腿、露沟等 2是正常
            elif porn_lbl in [1,2]:
                res_dict={'nsfw_prob': lbl_rate, 'sfw_prob': 1-lbl_rate, 'info': output[1]}
            else:
                assert(False,"porn_lbl is '%s' , it should only has three stat as 0,1,2" % porn_lbl)
        else:
            res_dict = get_default_res(state)
        json_str = json.dumps({"result":res_dict})
        # 超时检测
        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms")
        if total_delta > TIMEOUT*1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms")
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)

# custom模型弃用，使用图普/网易提供的第三方鉴黄
def predict_(request):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])
        id_ = params['id']
        # 拼接子服务的请求url
        request_urls = []
        for serv in sub_services:
            port=CONFIG_NEW[serv.NAME].port
            ser_name=serv.NAME
            request_urls.append(f"http://{HOST}:{port}/{ser_name}?img_url={img_url}&id={id_}")
        
        # 拼接一些 request_service_http_multiProcess 必须的参数
        service_info_list=[{
            "NAME":serv.NAME,
            "TIMEOUT":serv.TIMEOUT,
            "default_res":serv.get_default_res()} for serv in sub_services]

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
            else:
                logger.info(f"[id]:{id_} [SERVICE]:{ser_name} [delta]: {delta_t} [res]:{res}")
                if ser_name == NSFW_OBJ.NAME:
                    obj_score=max([i['prob'] for i in res]) if len(res)>0 else 0.0
                    # 物体检测针对的是裸露器官，加上0.3在目标检测中就算是可靠阈值
                    # 所以实际作为鉴黄分数和bcnn一起使用的时候要加倍或者其他放大方式
                    # 这里实现方式是做了个映射obj的判定分数是0.3~1.0 这里ensemble最后的判定分数是0.85~1.0
                    # 为了实现，obj只要检测到就认为是黄图，映射函数f为f(0.3)=0.85 & f(1.0)=f(1.0)
                    # EDIT: 修订为f(0.3)=0.5更合理，这里只是0.3相当于bcnn里0.5的判定阈值,0.85是profile里业务取的阈值，不应该挂钩
                    # a * obj_score + b = obj_score_new
                    a=(1.0-0.5)/(1-nsfw_obj_service.obj_prob_hold)
                    b=1-a
                    obj_score_new=a*obj_score+b
                    # 注意如果obj_score太小了，例如极端情况0时，这里还会映射为b的大小
                    # 即一张完全正常的图什么都检测不到，也会认为其有2/7=0.286的黄图概率
                    # 所以调整一下区间，0.1以上的时候使用 [0.3,1.0]=>[0.5,1.0] 的映射 其他时候保持原样
                    if obj_score>=0.1:
                        obj_score = obj_score_new
                    if  obj_score > nsfw_score:
                        nsfw_score = obj_score
                elif ser_name == NSFW_CLF.NAME:
                    clf_score=res["nsfw_prob"]
                    if  clf_score > nsfw_score:
                        nsfw_score = clf_score
                else:
                    assert False,f"ser_name:{ser_name} not in sub_service_names [{NSFW_OBJ.NAME}, {NSFW_CLF.NAME}]"
        if nsfw_score > -1:
            nsfw_score = round(float(nsfw_score), 4) 
            sfw_score = round(float(1-nsfw_score), 4)
            res=[sfw_score, nsfw_score]
            res_dict={'nsfw_prob': res[1], 'sfw_prob': res[0], 'info': output[np.argmax(res)]}
        else:
            res_dict=get_default_res("both clf&obj failed")
        json_str = json.dumps({"result":res_dict})

        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")
        if total_delta > TIMEOUT*1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")

        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)


