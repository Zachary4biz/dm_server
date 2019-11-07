# author: zac
# create-time: 2019-11-06 19:44
# usage: -

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ['TFHUB_CACHE_DIR'] = os.path.dirname(__file__)+"/model"
from zac_pyutils import CVUtils
import time
import json
from util import common_util
from django.conf import settings
from urllib.parse import unquote
from config import CONFIG_NEW
from django.http import HttpResponse
from util.cv_util import CVUtil

NAME = "vectorize"
TIMEOUT = CONFIG_NEW[NAME].timeout
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
transformer = CVUtils.Vectorize.VectorFromNN.InceptionV3()


def _predict(img):
    try:
        res = [float(i) for i in transformer.imgPIL2vec(img)]
        return res, "success"
    except Exception as e:
        logger.error(e)
        return None, repr(e)


#################
# Django API part
#################
param_check_list = ['img_url', 'id']


def get_default_res(info="default res"):
    return {'vector': [], 'info': info}


def predict(request):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])
        imgPIL, delta_t = common_util.timeit(cvUtil.img_from_url_PIL, img_url)
        logger.debug(u"[elapsed-load img]: {} [url]: {}".format(img_url, delta_t))
        if imgPIL is None:
            logger.error("at [id]: {} load img fail from [ur]: {}".format(params['id'], img_url))
            json_str = json.dumps({"result": get_default_res(info='load img fail')})
        else:
            res, remark = _predict(imgPIL)
            if res is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
            else:
                json_str = json.dumps({"result": res})

        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str[:100]} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")
        if total_delta > TIMEOUT * 1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str[:100]} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")

        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)
