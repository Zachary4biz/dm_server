# encoding:utf-8
# author: zac
# create-time: 2019-07-09 15:31
# usage: - 
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/../../")
import json
import requests
from util import config, common_util
from util.logger import Logger
from apps.age import age_service
from apps.gender import gender_service
from apps.nsfw import nsfw_service
from apps.obj_detection import yolo_service
from config import *
import time
import timeout_decorator
from zac_pyutils.Timeout import TimeoutThread, TimeoutProcess

logger = None


def get_logger():
    global logger
    if logger is None:
        logger = Logger('cutcut_profile', log2console=False, log2file=True, logfile=config.CUTCUT_LOG_PATH, logfile_err="auto").get_logger()
    return logger


def request_kw(text, is_title=True):
    keywords = []  # default
    try:
        res = requests.post(config.NLP.kw_port,
                            data={"sentences": text, "isShortText": "1" if is_title else "0", "topn": 2})
        if res.status_code == 200 and len(res.text.strip()) > 0:
            keywords = [i.split(":") for i in res.text.strip().split("\t")]
            keywords = [{"keyword": kw, "weight": score} for kw, score in keywords]
    except Exception as e:
        get_logger().error(e)
    return keywords


def request_nlp(title, content):
    if title or content:
        try:
            title_kw = request_kw(title, is_title=True)
            content_kw = request_kw(content, is_title=False)
            nlp_res = {"title_keywords": title_kw, "content_keywords": content_kw}
        except Exception as e:
            get_logger().error(repr(e))
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


def request_service_http(service, inner_request):
    url, id_ = inner_request.GET['img_url'], inner_request.GET['id']
    begin = time.time()
    request_url = "http://{}:{}/{}?img_url={}&id={}".format(HOST, CONFIG[service.NAME]['port'], service.NAME, url, id_)
    get_logger().debug(">>> service:{}, request_url:{}".format(service.NAME, request_url))
    try:
        res = requests.get(request_url, timeout=service.TIMEOUT).text
        res = json.loads(res)['result']
    except Exception as e:
        get_logger().error(e)
        res = service.get_default_res()
    get_logger().debug(">>> service:{}, res:{}, request_url:{}".format(service.NAME, res, request_url))
    delta = "{:.2f}ms".format(round(time.time() - begin, 5) * 1000)
    return res, delta


def request_service(service, inner_request):
    default = service.get_default_res()
    msg = "timeout at {} in {} sec".format(str(service.NAME), service.TIMEOUT)

    @timeout_decorator.timeout(seconds=service.TIMEOUT, use_signals=False, exception_message=msg)
    def request(inner_request_):
        get_logger().info("begin predict ..")
        ress = service.predict(inner_request_).content
        get_logger().info("predict end")
        res_ = json.loads(ress)['result']
        return res_

    begin = time.time()
    try:
        get_logger().info("begin request by {}".format(service.NAME))
        res = request(inner_request)
    except Exception as e:
        get_logger().error(e)
        res = default
    delta = "{:.2f}ms".format(round(time.time() - begin, 5) * 1000)
    return res, delta


def _request(service, inner_request_):
    get_logger().debug("[pid]: {} [service]: {} begin predict ..".format(os.getpid(), service.NAME))
    ress = service.predict(inner_request_).content
    get_logger().debug("[pid]: {} [service]: {} predict end".format(os.getpid(), service.NAME))
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
        get_logger().debug(u" [img_url]:{} [id]:{} [title]:{} [desc]:{}".format(img_url, id_, title[:50], desc[:50]))
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

        nsfw_res, nsfw_time = request_service_http(nsfw_service, inner_request)
        age_res, age_time = request_service_http(age_service, inner_request)
        gender_res, gender_time = request_service_http(gender_service, inner_request)
        yolo_res, yolo_time = request_service_http(yolo_service, inner_request)

        is_nsfw = 1 if nsfw_res['id'] == 1 and nsfw_res['prob'] >= 0.8 else 0  # 异常时填充值为 id:-1,prob:1.0
        nlp_res_dict = request_nlp(title, desc) # get NLP features

        res_dict.update({"age": age_res, "gender": gender_res, "obj": yolo_res, "ethnic": [], "nsfw": nsfw_res,
                         "review_status": [is_nsfw], "status": "success"})
        res_dict.update(nlp_res_dict)
        res_jsonstr = json.dumps(res_dict)
        total_time = "{:.2f}ms".format(round(time.time() - begin, 5) * 1000)
        get_logger().info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed]: total:{} = nsfw:{} + age:{} + gender:{} + yolo:{} ".format(id_, img_url,
                                                                                                           res_jsonstr,
                                                                                                           total_time,
                                                                                                           nsfw_time,
                                                                                                           age_time,
                                                                                                           gender_time,yolo_time))
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


