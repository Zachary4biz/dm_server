# encoding:utf-8
# author: zac
# create-time: 2019-07-09 15:31
# usage: - 
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import copy
import requests
from age import age_service
from gender import gender_service
# from nsfw import nsfw_service
from nonage import nonage_service
from nsfw import nsfw_ensemble_service
from obj_detection import yolo_service
from ethnicity import ethnicity_service
from config import CONFIG_NEW, NLP
import time
from urllib.parse import quote, unquote, urlparse, urlencode

from multiprocessing import Pool
import traceback
from django.conf import settings

NAME = "cutcut_profile"
logger = settings.LOGGER[NAME]
nsfw_threshold = 0.8
nonage_threshold = 0.5


def request_kw(text, is_title=True):
    keywords = []  # default
    try:
        res = requests.post(NLP.kw_port,
                            data={"sentences": text, "isShortText": "1" if is_title else "0", "topn": 2})
        if res.status_code == 200 and len(res.text.strip()) > 0:
            keywords = [i.split(":") for i in res.text.strip().split("\t")]
            keywords = [{"keyword": kw, "weight": score} for kw, score in keywords]
    except Exception as e:
        logger.error(e)
    return keywords


def request_nlp(title, content):
    if title or content:
        try:
            title_kw = request_kw(title, is_title=True)
            content_kw = request_kw(content, is_title=False)
            nlp_res = {"title_keywords": title_kw, "content_keywords": content_kw}
        except Exception as e:
            logger.error(repr(e))
            nlp_res = {"title_keywords": [], "content_keywords": []}
    else:
        nlp_res = {"title_keywords": [], "content_keywords": []}
    return nlp_res


#################
# Django API part
#################
from django.http import HttpResponse
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

param_check_list = ['img_url', 'id', 'title', 'description']
HOST = os.environ.get("SERVICE_HOST")


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


# inplace and return
# nsfw的结果要多处理一层：{'nsfw_prob': 0.89, 'sfw_prob': 0.11} ==> {'id':1, 'prob':0.89, 'info':'nsfw pic'}
def update_nsfw(inp_res, key="nsfw", inplace=True):
    inp_nsfw, nsfw_time, nsfw_success = inp_res[key]
    if inp_nsfw['nsfw_prob'] >= nsfw_threshold:
        # 只有超过阈值(0.85)才在结果中展示为nsfw pic
        nsfw_res = {'id': 1, 'prob': inp_nsfw['nsfw_prob'], 'info': 'nsfw pic'}
    elif inp_nsfw['nsfw_prob'] == -1:
        # 返回的是默认值，说明请求异常
        nsfw_success = "fail"
        nsfw_res = {'id': -1, 'prob': 1.0, 'info': inp_nsfw['info']}
    else:
        nsfw_res = {'id': 0, 'prob': inp_nsfw['sfw_prob'], 'info': 'normal pic'}

    if inplace:
        inp_res.update({key: (nsfw_res, nsfw_time, nsfw_success)})
        return inp_res
    else:
        inp_res_ = copy.deepcopy(inp_res)
        inp_res_.update({key: (nsfw_res, nsfw_time, nsfw_success)})
        return inp_res_


@csrf_exempt
def profile_direct_api(request):
    params = request.POST
    begin = time.time()
    # params-check
    if all(i in params for i in param_check_list):
        img_url = params.get("img_url")
        parts = urlparse(img_url)
        build_url = parts._replace(query=urlencode({"mode": 0, "w": 800, "h": 800})).geturl()
        img_url = quote(build_url)
        id_ = params.get("id")
        title = params.get("title")
        desc = params.get("description")
        logger.debug(u" [img_url]:{} [id]:{} [title]:{} [desc]:{}".format(img_url, id_, title[:50], desc[:50]))
        # features
        res_dict = {}
        # CV features
        inner_request = HttpRequest()
        inner_request.method = "GET"
        inner_request.GET = {"img_url": img_url, "id": id_}

        p = Pool(4)
        service_list_ = [nsfw_ensemble_service, nonage_service, age_service, gender_service, yolo_service, ethnicity_service]
        service_list = [{'NAME': i.NAME, 'TIMEOUT': i.TIMEOUT, 'default_res': i.get_default_res()} for i in service_list_]
        url_list = ["http://{}:{}/{}?img_url={}&id={}".format(HOST, CONFIG_NEW[service['NAME']].port, service['NAME'], img_url, id_) for service in service_list]*len(service_list)
        r = p.map(func=request_service_http_multiProcess, iterable=list(zip(service_list, url_list)))
        # 多进程结果顺序和输入服务的顺序一样，zip到一起避免后续取数据的时候出错
        result = dict(zip([i['NAME'] for i in service_list], r))
        p.close()
        p.join()
        # 取出标记检查是否为success
        for k, v in result.items():
            res, delta_t, is_success = v
            if is_success != "success":
                # print(is_success)
                logger.error("[SERVICE]:{} [id]:{} [ERR]:{}".format(k, id_, is_success.split("\t")[0]))
                logger.debug(is_success)
        # 根据阈值nsfw_threshold更新result里nsfw的结果 
        update_nsfw(result, key=nsfw_ensemble_service.NAME,inplace=True)
        nsfw_res, _, _ = result[nsfw_ensemble_service.NAME]
        nonage_res,_,_ = result[nonage_service.NAME]
        # 更新review_status 
        if nsfw_res['id'] == 1:
            # 色情图片下线
            res_dict.update({"review_status": [1]})
        elif nonage_res['rate'] >= nonage_threshold:
            # 未成年人先发后审
            res_dict.update({"review_status": [2]})
        else:
            # 其他不做review
            res_dict.update({"review_status": [0]})

        # 如果id标记为-1表示nsfw检测服务异常了，这类图标记为先发后审
        if nsfw_res['id'] == -1:
            res_dict.update({"review_status": [2]})

        res_dict.update({info['NAME']: result[info['NAME']][0] for info in service_list})
        # get NLP features
        nlp_res_dict = request_nlp(title, desc)
        res_dict.update(nlp_res_dict)
        final_status = "success" if all(i == "success" for i in [is_success for k, (res, delta_t, is_success) in result.items()]) else "fail"
        res_dict.update({"status": final_status})
        # 'nsfw_ensemble'键名替换为'nsfw'，兼容历史下游服务
        res_dict['nsfw']=res_dict.pop(nsfw_ensemble_service.NAME)
        # 最终json结果
        res_jsonstr = json.dumps(res_dict)
        # 计时与日志
        total_time = round(time.time() - begin, 5) * 1000
        sub_service_time = " + ".join([f"{i['NAME']}:{result[i['NAME']][1]:.2f}ms" for i in service_list])
        logger.info(f"[id]: {id_} [img_url]: {unquote(img_url)} [res]: {res_jsonstr} [elapsed]: total:{total_time:.2f}ms = {sub_service_time}")

        return HttpResponse(res_jsonstr, status=200, content_type="application/json,charset=utf-8")

    else:
        return HttpResponse("use POST(form), params: '{}'".format(",".join(param_check_list)), status=400)


def default_profile(request):
    res = {
        "age": [],
        "gender": [],
        "ethnic": [],
        "obj": [],
        "nsfw": {},
        "review_status": [2],
        "title_keywords": [],
        "content_keywords": [],
        "status": "fail"
    }
    json_str = json.dumps(res)
    return HttpResponse(json_str, status=200)


# todo 内部by code调用各个service
@csrf_exempt
def profile(request):
    pass


