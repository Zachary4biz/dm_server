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
os.environ['GLOG_minloglevel'] = '2'
from config import CONFIG_NEW
from util.logger import Logger
from util import common_util
from util.cv_util import CVUtil
from django.conf import settings

NAME = "age"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = [
    '71+ years',
    '36 - 50 years',
    '51 - 70 years',
    '6 - 15 years',
    '0 - 5 years',
    '16 - 25 years',
    '26 - 35 years'
]
cvUtil = CVUtil()
logger = settings.LOGGER
modelClassifier = settings.ALGO_MODEL


def get_default_res(info="default res"):
    return [{'id': -1, 'prob': 1.0, 'info': info}]


# 专用于predict切分人脸后的图像(caffe io下的格式)
def _predict_face_caffe_img(face):
    pred = modelClassifier.predict(face)[0]
    confidence = round(float(pred[pred.argmax()]), 4)
    return {"id": int(pred.argmax()), "prob": confidence}


def _predict(img):
    face_list, delta_t = common_util.timeit(cvUtil.get_face_list, img)
    logger.debug("[elapsed-dlib face]:{}".format(delta_t))
    if len(face_list) == 0:
        return None, "no frontal-face detected."
    else:
        face_list = [cvUtil.pre_cv2caffe(i) for i in face_list]
        res_list = []
        for face in face_list:
            res_list.append(_predict_face_caffe_img(face))
        return res_list, "success"


#############
# Test case
#############
# 正脸：https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg
# 侧脸成功：
# 	http://i1.sinaimg.cn/lx/beauty/liangli/p/2010/0925/U318P8T1D1011021F913DT20100816145616.jpg
#	http://n.sinaimg.cn/front/241/w552h489/20190204/vYlJ-hsmkfyp5208900.jpg 
# 侧脸失败：
#	http://d.ifengimg.com/w600/p0.ifengimg.com/pmop/2017/0401/9DD196DAB4A44CF6AC37190B7907ACD755B56F9F_size29_w626_h586.jpeg 
# 夸张表情失败：
#	https://s9.rr.itc.cn/r/Q/Iv/IzaIf6j.jpg

# imgURL = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg"
# _predict(cvUtil.img_from_url_cv2(imgURL))

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
        logger.debug("[elapsed-load img]: {}  [url]: {}".format(params['img_url'], delta_t))
        if img is None:
            json_str = json.dumps({"result": get_default_res(info='load image fail')})
            logger.error("at [id]: {} load img fail [ur]: {}".format(params['id'], params['img_url']))
        else:
            (res_list, remark) = _predict(img)
            if res_list is None:
                json_str = json.dumps({"result": get_default_res(info=remark)})
                logger.warn("at [id]: {} [res]: {} [remark]: {}".format(params['id'], json_str, remark))
            else:
                [d.update({"info": output[d['id']]}) for d in res_list]
                json_str = json.dumps({"result": res_list})
                logger.info("at [id]: {} [res]: {}".format(params['id'], json_str))
        logger.info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed-total]: {}ms [elapsed-load img]: {}ms".format(params['id'], params['img_url'], json_str,
                                                                       round(time.time() - begin, 5) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)

