# author: zac
# create-time: 2019-12-18 12:17
# usage: - 

import json
import time
from util import common_util
from django.http import HttpResponse
from urllib.parse import unquote


def api_format_predict(request, logger, param_check_list, load_img_func, get_default_res, _predict, TIMEOUT):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img_url = unquote(params['img_url'])
        img, delta_t = common_util.timeit(load_img_func, img_url)
        logger.debug("[elapsed-load img]: {}  [url]: {}".format(img_url, delta_t))
        if img is None:
            json_str = json.dumps({"result": get_default_res(info='load image fail')})
            logger.error("at [id]: {} load img fail [ur]: {}".format(params['id'], img_url))
        else:
            (res_list, remark) = _predict(img)
            if res_list is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
                logger.warn("at [id]: {} [res]: {} [remark]: {}".format(params['id'], json_str, remark))
            else:
                # [d.update({"info": output[d['id']]}) for d in res_list]
                json_str = json.dumps({"result": res_list})
                logger.info("at [id]: {} [res]: {}".format(params['id'], json_str))
        total_delta = round(time.time() - begin, 5) * 1000
        logger.info(f"[id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")
        if total_delta > TIMEOUT*1000:
            logger.error(f"[TIMEOUT] [id]: {params['id']} [img_url]: {img_url} [res]: {json_str} [ELA-total]: {total_delta:.2f}ms [ELA-img]: {delta_t:.2f}ms")

        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)

