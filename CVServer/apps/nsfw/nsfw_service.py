# encoding=utf-8

##########
# prepare
##########
import json
import time
from ...util.logger import Logger
from ...util import config
from ...util import common_util
from ...util.cv_util import CVUtil

logger = Logger('nsfw_service', log2console=False, log2file=True, logfile=config.NSFW_LOG_PATH).get_logger()

#########
# cv part
#########
import os
os.environ['GLOG_minloglevel'] = '2'

basePath = os.path.dirname(__file__)
cvUtil = CVUtil()
modelClassifier = cvUtil.load_model(prototxt_fp=basePath + "/model/nsfw_deploy.prototxt",
                                    caffemodel_fp=basePath + "/model/resnet_50_1by2_nsfw.caffemodel")

TIMEOUT = 5
NAME = "nsfw_service"
output = [
    'normal pic',
    'nsfw pic'
]


def get_default_res(info="default res"):
    return {'id': -1, 'prob': 1.0, 'info': info}


def _predict(img):
    try:
        img_pro = cvUtil.pre_cv2caffe(img)
        pred = modelClassifier.predict(img_pro)[0]
        confidence = round(pred[pred.argmax()], 4)
        return {"id": int(pred.argmax()), "prob": confidence}, "success"
    except Exception as e:
        logger.error(e)
        return None, repr(e.message)


#############
# Test case
#############
imgURL = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg"
print(_predict(cvUtil.img_from_url_cv2(imgURL)))

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
            u"[id]: {} [img_url]: {} [res]: {} [elapsed]: {}ms [elapsed-load img]: {}ms".format(params['id'], params['img_url'], json_str,
                                                                       round(time.time() - begin, 5) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)
