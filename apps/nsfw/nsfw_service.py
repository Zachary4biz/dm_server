# encoding=utf-8

##########
# prepare
##########
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import os
os.environ['GLOG_minloglevel'] = '2'  # 控制caffe日志
from config import CONFIG_NEW
from util.logger import Logger
from util import common_util
from util.cv_util import CVUtil
from django.conf import settings


NAME = "nsfw"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['normal pic', 'nsfw pic']
cvUtil = CVUtil()
logger = settings.LOGGER
modelClassifier = settings.ALGO_MODEL


def get_default_res(info="default res"):
    return {'id': -1, 'prob': 1.0, 'info': info}


def _predict(img):
    try:
        img_pro = cvUtil.pre_cv2caffe(img)
        pred = modelClassifier.predict(img_pro)[0]
        confidence = round(float(pred[pred.argmax()]), 4)
        return {"id": int(pred.argmax()), "prob": confidence}, "success"
    except Exception as e:
        logger.error(e)
        return None, repr(e.message)


#############
# Test case
#############
imgURL = "http://scd.cn.rfi.fr/sites/chinese.filesrfi/dynimagecache/0/0/660/372/1024/578/sites/images.rfi.fr/files/aef_image/_98711473_042934387-1.jpg"
# from zac_pyutils.Timeout import TimeoutThread
# from zac_pyutils.ExqUtils import zprint
# target_thread = TimeoutThread(target=_predict, args=(cvUtil.img_from_url_cv2(imgURL), ), time_limit=TIMEOUT)
# zprint("[nsfw] begin target_thread")
# res = target_thread.start()
# print("res is:", res)
# print(_predict(cvUtil.img_from_url_cv2(imgURL)))

#################
# Django API part
#################
from django.http import HttpResponse

param_check_list = ['img_url', 'id']


def predict(request):
    begin = time.time()
    params = request.GET
    if all(i in params for i in param_check_list):
        img, delta_t = common_util.timeit(cvUtil.img_from_url_cv2, params['img_url'])
        logger.debug(u"[elapsed-load img]: {} [url]: {}".format(params['img_url'], delta_t))
        if img is None:
            logger.error("at [id]: {} load img fail from [ur]: {}".format(params['id'], params['img_url']))
            json_str = json.dumps({"result": get_default_res(info='load img fail')})
        else:
            res, remark = _predict(img)
            if res is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
            else:
                res.update({"info": output[res['id']]})
                json_str = json.dumps({"result": res})
        logger.info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed]: {:.2f}ms [elapsed-load img]: {:.2f}ms".format(params['id'], params['img_url'], json_str,
                                                                       round(time.time() - begin, 5) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)


