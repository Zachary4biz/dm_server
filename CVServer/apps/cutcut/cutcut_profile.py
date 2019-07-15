# encoding:utf-8
# author: zac
# create-time: 2019-07-09 15:31
# usage: - 

import json
import requests
from ...util import config
from ...util.logger import Logger
from ...apps.age import age_service
from ...apps.gender import gender_service
from ...apps.nsfw import nsfw_service
import time

logger = Logger('cutcut_profile', log2console=False, log2file=True, logfile=config.CUTCUT_LOG_PATH).get_logger()


def request_kw(text, is_title=True):
    keywords = []  # default
    try:
        res = requests.post(config.NLP.kw_port,
                            data={"sentences": text, "isShortText": "1" if is_title else "0", "topn": 2})
        if res.status_code == 200 and len(res.text.strip()) > 0:
            keywords = [i.split(":") for i in res.text.strip().split("\t")]
            keywords = [{"keyword": kw, "weight": score} for kw, score in keywords]
    except Exception as e:
        logger.error(e)
    return keywords


def request_nlp(title, content):
    try:
        title_kw = request_kw(title, is_title=True)
        content_kw = request_kw(content, is_title=False)
        nlp_res = {"title_keywords": title_kw, "content_keywords": content_kw}
    except Exception as e:
        logger.error(repr(e))
        nlp_res = {"title_keywords": [], "content_keywords": []}
    return nlp_res


#################
# Django API part
#################
from django.http import HttpResponse
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt

param_check_list = ['img_url', 'id', 'title', 'description']


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

        nsfw_res = json.loads(nsfw_service.predict(inner_request).content)["result"]
        is_nsfw = 1 if nsfw_res['id'] == 1 and nsfw_res['prob'] >= 0.8 else 0  # 异常时填充值为 id:-1,prob:1.0
        age_res = json.loads(age_service.predict(inner_request).content)["result"]
        gender_res = json.loads(gender_service.predict(inner_request).content)["result"]
        # NLP features
        nlp_res_dict = request_nlp(title, desc)
        # return
        res_dict.update({"age": age_res, "gender": gender_res, "ethnic": [], "nsfw": nsfw_res, "review_status": [is_nsfw], "status":"success"})
        res_dict.update(nlp_res_dict)
        res_jsonstr = json.dumps(res_dict)
        logger.info(u"[id]: {} [img_url]: {} [res]: {} [elapsed]: {}ms".format(id_, img_url, res_jsonstr,
                                                                               round(time.time() - begin, 5) * 1000))
        return HttpResponse(res_jsonstr, status=200, content_type="application/json,charset=utf-8")

    else:
        return HttpResponse("use POST(form), params: '{}'".format(",".join(param_check_list)), status=400)


def default_profile(request):
    res = {
        "age": [],
        "gender": [],
        "ethnic": [],
        "nsfw": {},
        "review_status": [0],
        "title_keywords": [],
        "content_keywords": [],
        "status":"fail"
    }
    json_str = json.dumps(res)
    return HttpResponse(json_str, status=200)


# todo 内部by code调用各个service
@csrf_exempt
def profile(request):
    pass
