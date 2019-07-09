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

logger = Logger('cutcut_profile', log2console=False, log2file=True, logfile=config.CUTCUT_LOG_PATH).get_logger()


def request_kw(text, is_title=True):
    keywords = []  # default
    try:
        res = requests.post(config.NLP.kw_port,
                            data={"sentences": text, "isShortText": "1" if is_title else "0", "topn": 2})
        if res.status_code == 200:
            keywords = [i.split(":") for i in res.text.split("\t")]
            keywords = [{"keyword": kw, "weight": score} for kw, score in keywords]
    except Exception as e:
        logger.error(e)
    return keywords


def request_nlp(title, content):
    title_kw = request_kw(title, is_title=True)
    content_kw = request_kw(content, is_title=False)
    nlp_res = {"title_keywords": title_kw, "content_keywords": content_kw}
    return nlp_res


#################
# Django API part
#################
from django.http import HttpResponse
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def profile(request):
    if request.method == "POST":
        # params-check
        params = request.POST
        img_url = params.get("img_url")
        id_ = params.get("id")
        title = params.get("title")
        desc = params.get("description")
        logger.debug(" [img_url]:{} [id]:{} [title]:{} [desc]:{}".format(img_url, id_, title, desc))
        # features
        res_dict = {}
        # CV features
        inner_request = HttpRequest()
        inner_request.method = "GET"
        inner_request.GET = {"img_url": img_url, "id": id_}
        age_res = json.loads(age_service.predict(inner_request))["result"]
        gender_res = json.loads(gender_service.predict(inner_request))["result"]
        nsfw_res = json.loads(nsfw_service.predict(inner_request))["result"]
        # NLP features
        nlp_res_dict = request_nlp(title, desc)
        # return
        res_dict.update({"age": age_res, "gender": gender_res, "nsfw_res": nsfw_res})
        res_dict.update(nlp_res_dict)
        res_jsonstr = json.dumps(res_dict)
        logger.info(res_jsonstr)
        return HttpResponse(res_jsonstr, status=200)

    else:
        return HttpResponse("use POST, param: 'title', 'description','img_ur','id'", status=400)
