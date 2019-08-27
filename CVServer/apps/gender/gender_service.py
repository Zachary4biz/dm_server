# encoding=utf-8

##########
# prepare
##########
import json
import time
from ...util.logger import Logger
from ...util import config
from ...util.common_util import timeit
from ...util.cv_util import CVUtil

logger = Logger('gender_service', log2console=False, log2file=True, logfile=config.GENDER_LOG_PATH).get_logger()

#########
# cv part
#########
import sys
import os
os.environ['GLOG_minloglevel'] = '2'

basePath = os.path.dirname(__file__)
cvUtil = CVUtil()
modelClassifier = cvUtil.load_model(prototxt_fp=basePath + "/model/gender_deploy_correct.prototxt",
                                    caffemodel_fp=basePath + "/model/gender_model_correct.caffemodel")

TIMEOUT = 4
NAME = "gender_service"
output = [
    'female',
    'male',
]


def get_default_res(info="default res"):
    return [{'id': -1, 'prob': 1.0, 'info': info}]


# 专用于predict切分人脸后的图像(caffe io下的格式)
def _predict_face_caffe_img(face):
    pred = modelClassifier.predict(face)[0]
    confidence = round(pred[pred.argmax()], 4)
    return {"id": pred.argmax(), "prob": confidence}


def _predict(img):
    face_list, delta_t = timeit(cvUtil.get_face_list, img)
    logger.debug("[elapsed-dlib face]:{}".format(delta_t))
    # face_list = cvUtil.get_face_list(img)
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
# imgURL = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg"
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
        img, delta_t = timeit(cvUtil.img_from_url_cv2, params['img_url'])
        logger.debug("[elapsed-load img]: {} [url]: {}".format(params['img_url'], delta_t))
        if img is None:
            # 图片加载失败
            json_str = json.dumps({"result": get_default_res(info="load img fail")})
            logger.error("at [id]: {} load img fail [ur]: {}".format(params['id'], params['img_url']))
        else:
            # 图片加载完毕
            (res_list, remark) = _predict(img)
            if res_list is None:
                # predict失败
                json_str = json.dumps({"result": get_default_res(info=remark)})
                logger.warn("at [id]: {} [res]: {} [remark]: {}".format(params['id'], json_str, remark))
            else:
                # 正常返回
                [d.update({"info": output[d['id']]}) for d in res_list]
                json_str = json.dumps({"result": res_list})
                logger.info("at [id]: {} [res]: {}".format(params['id'], json_str))
        logger.info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed-total]: {}ms [elapsed-load img]: {}ms".format(params['id'], params['img_url'], json_str,
                                                                       round(time.time() - begin, 5) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)
