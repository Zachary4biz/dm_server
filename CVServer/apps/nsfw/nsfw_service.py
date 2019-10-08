# encoding=utf-8

##########
# prepare
##########
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__))+"/../../")
import json
import time
from util.logger import Logger
from util import config
from util import common_util
from util.cv_util import CVUtil

logger = None


def get_logger():
    global logger
    if logger is None:
        logger = Logger('nsfw_service', log2console=False, log2file=True, logfile=config.NSFW_LOG_PATH).get_logger()
    return logger

#########
# cv part
#########
import os
os.environ['GLOG_minloglevel'] = '2'

basePath = os.path.abspath(os.path.dirname(__file__))
cvUtil = CVUtil()
modelClassifier = None


def get_clf():
    global modelClassifier
    if modelClassifier is None:
        get_logger().info(">>> loading clf (should be init)")
        modelClassifier = cvUtil.load_model(prototxt_fp=basePath + "/model/nsfw_deploy.prototxt",
                                            caffemodel_fp=basePath + "/model/resnet_50_1by2_nsfw.caffemodel")
    return modelClassifier


TIMEOUT = 5
NAME = "nsfw"
output = [
    'normal pic',
    'nsfw pic'
]


def get_default_res(info="default res"):
    return {'id': -1, 'prob': 1.0, 'info': info}


def _predict(img):
    try:
        img_pro = cvUtil.pre_cv2caffe(img)
        pred = get_clf().predict(img_pro)[0]
        confidence = round(float(pred[pred.argmax()]), 4)
        return {"id": int(pred.argmax()), "prob": confidence}, "success"
    except Exception as e:
        get_logger().error(e)
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
        get_logger().debug(u"[elapsed-load img]: {} [url]: {}".format(params['img_url'], delta_t))
        if img is None:
            get_logger().error("at [id]: {} load img fail from [ur]: {}".format(params['id'], params['img_url']))
            json_str = json.dumps({"result": get_default_res(info='load img fail')})
        else:
            res, remark = _predict(img)
            if res is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
            else:
                res.update({"info": output[res['id']]})
                json_str = json.dumps({"result": res})
        get_logger().info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed]: {:.2f}ms [elapsed-load img]: {:.2f}ms".format(params['id'], params['img_url'], json_str,
                                                                       round(time.time() - begin, 5) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)
