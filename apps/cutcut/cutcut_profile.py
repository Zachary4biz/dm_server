# encoding:utf-8
# author: zac
# create-time: 2019-07-09 15:31
# usage: - 
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import json
import requests
from age import age_service
from gender import gender_service
from nsfw import nsfw_service
from obj_detection import yolo_service
from config import CONFIG_NEW, NLP
import time
import timeout_decorator
from zac_pyutils.Timeout import TimeoutThread, TimeoutProcess
from multiprocessing import Pool
import traceback
from django.conf import settings

NAME = "cutcut_profile"
logger = settings.LOGGER[NAME]


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


def request_service_http(service, inner_request):
    url, id_ = inner_request.GET['img_url'], inner_request.GET['id']
    begin = time.time()
    request_url = "http://{}:{}/{}?img_url={}&id={}".format(HOST, CONFIG_NEW[service.NAME].port, service.NAME, url, id_)
    logger.debug(">>> service:{}, request_url:{}".format(service.NAME, request_url))
    try:
        res = requests.get(request_url, timeout=service.TIMEOUT).text
        res = json.loads(res)['result']
    except Exception as e:
        logger.error(e)
        res = service.get_default_res()
    logger.debug(">>> service:{}, res:{}, request_url:{}".format(service.NAME, res, request_url))
    delta = "{:.2f}ms".format(round(time.time() - begin, 5) * 1000)
    return res, delta


def request_service(service, inner_request):
    default = service.get_default_res()
    msg = "timeout at {} in {} sec".format(str(service.NAME), service.TIMEOUT)

    @timeout_decorator.timeout(seconds=service.TIMEOUT, use_signals=False, exception_message=msg)
    def request(inner_request_):
        logger.info("begin predict ..")
        ress = service.predict(inner_request_).content
        logger.info("predict end")
        res_ = json.loads(ress)['result']
        return res_

    begin = time.time()
    try:
        logger.info("begin request by {}".format(service.NAME))
        res = request(inner_request)
    except Exception as e:
        logger.error(e)
        res = default
    delta = "{:.2f}ms".format(round(time.time() - begin, 5) * 1000)
    return res, delta


def _request(service, inner_request_):
    logger.debug("[pid]: {} [service]: {} begin predict ..".format(os.getpid(), service.NAME))
    ress = service.predict(inner_request_).content
    logger.debug("[pid]: {} [service]: {} predict end".format(os.getpid(), service.NAME))
    res_ = json.loads(ress)['result']
    return res_


def request_service_process_timeout(service, inner_request):
    target_p = TimeoutProcess(target=_request, args=(service, inner_request,), time_limit=service.TIMEOUT)
    begin = time.time()
    res = target_p.start()
    res = res if res is not None else service.get_default_res()
    delta = "{:.2f}ms".format(round(time.time() - begin, 5) * 1000)
    return res, delta


def request_service_thread_timeout(service, inner_request):
    target_thread = TimeoutThread(target=_request, args=(service, inner_request, ), time_limit=service.TIMEOUT)
    begin = time.time()
    res = target_thread.start()
    res = res if res is not None else service.get_default_res()
    delta = "{:.2f}ms".format(round(time.time() - begin, 5) * 1000)
    return res, delta


@csrf_exempt
def profile_direct_api(request):
    params = request.POST
    begin = time.time()
    # params-check
    if all(i in params for i in param_check_list):
        img_url = params.get("img_url")
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

        # nsfw_res, nsfw_time = request_service_thread_timeout(nsfw_service, inner_request)
        # age_res, age_time = request_service_thread_timeout(age_service, inner_request)
        # gender_res, gender_time = request_service_thread_timeout(gender_service, inner_request)
        # yolo_res, yolo_time = request_service_thread_timeout(yolo_service, inner_request)

        # nsfw_res, nsfw_time = request_service(nsfw_service, inner_request)
        # age_res, age_time = request_service(age_service, inner_request)
        # gender_res, gender_time = request_service(gender_service, inner_request)
        # yolo_res, yolo_time = request_service_process_timeout(yolo_service, inner_request)
        # yolo_res, yolo_time = yolo_service.get_default_res(), 0

        # nsfw_res, nsfw_time = request_service_http(nsfw_service, inner_request)
        # age_res, age_time = request_service_http(age_service, inner_request)
        # gender_res, gender_time = request_service_http(gender_service, inner_request)
        # yolo_res, yolo_time = request_service_http(yolo_service, inner_request)

        # class abc():
        #     def __init__(self):
        #         self.GET={"img_url": img_url, "id": id_}
        # inner_request = abc()

        p = Pool(4)
        service_list_ = [nsfw_service, age_service, gender_service, yolo_service]
        service_list = [{'NAME': i.NAME, 'TIMEOUT': i.TIMEOUT, 'default_res': i.get_default_res()} for i in service_list_]
        url_list = ["http://{}:{}/{}?img_url={}&id={}".format(HOST, CONFIG_NEW[service['NAME']].port, service['NAME'], img_url, id_) for service in service_list]*len(service_list)
        r = p.map(func=request_service_http_multiProcess, iterable=list(zip(service_list, url_list)))
        result = dict(zip([i['NAME'] for i in service_list], r))  # 多进程结果顺序和输入服务的顺序一样，zip到一起避免后续取数据的时候出错
        p.close()
        p.join()
        # 取出标记检查是否为success
        for k, v in result.items():
            res, delta_t, is_success = v
            if is_success != "success":
                # print(is_success)
                logger.error("[SERVICE]:{} [id]:{} [ERR]:{}".format(k, id_, is_success.split("\t")[0]))
                logger.debug(is_success)
        nsfw_res, nsfw_time, nsfw_success = result['nsfw']  # _ 是是否成功的标记，上面已经检查过并输出log了
        age_res, age_time, age_success = result['age']
        gender_res, gender_time, gender_success = result['gender']
        yolo_res, yolo_time, yolo_success = result['obj']

        is_nsfw = 1 if nsfw_res['id'] == 1 and nsfw_res['prob'] >= 0.8 else 0  # 异常时填充值为 id:-1,prob:1.0
        nlp_res_dict = request_nlp(title, desc)  # get NLP features

        res_dict.update({"age": age_res, "gender": gender_res, "obj": yolo_res, "ethnic": [], "nsfw": nsfw_res,
                         "review_status": [is_nsfw]})
        res_dict.update(nlp_res_dict)
        final_status = "success" if all(i == "success" for i in [nsfw_success, age_success, gender_success, yolo_success]) else "fail"
        res_dict.update({"status": final_status})
        res_jsonstr = json.dumps(res_dict)
        total_time = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {id_} [img_url]: {img_url} [res]: {res_jsonstr} [elapsed]: total:{total_time:.2f}ms = nsfw:{nsfw_time:.2f}ms + age:{age_time:.2f}ms + gender:{gender_time:.2f}ms + yolo:{yolo_time:.2f}ms ")

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
        "review_status": [0],
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


