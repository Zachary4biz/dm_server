# encoding=utf-8

##########
# prepare
##########
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ['GLOG_minloglevel'] = '2'
from config import CONFIG_NEW
from util import common_util
from util.cv_util import CVUtil
from django.conf import settings
from services import api_format_predict

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
logger = settings.LOGGER[NAME]
modelClassifier = settings.ALGO_MODEL[NAME]
load_img_func = cvUtil.img_from_url_cv2
param_check_list = ['img_url', 'id']


def get_default_res(info="default res"):
    return [{'id': -1, 'prob': 1.0, 'info': info}]


def _predict(img):
    face_list, delta_t = common_util.timeit(cvUtil.get_face_list, img)
    logger.debug("[elapsed-dlib face]:{}".format(delta_t))
    if len(face_list) == 0:
        return None, "no frontal-face detected."
    else:
        face_list = [cvUtil.pre_cv2caffe(i) for i in face_list]
        res_list = []
        for face in face_list:
            pred = modelClassifier.predict(face)[0]
            confidence = round(float(pred[pred.argmax()]), 4)
            res_list.append({"id": int(pred.argmax()), "prob": confidence, "info": output[int(pred.argmax())]})
        return res_list, "success"


def predict(request):
    return api_format_predict(request,
                              logger=logger, param_check_list=param_check_list,
                              load_img_func=load_img_func, get_default_res=get_default_res, _predict=_predict,
                              TIMEOUT=TIMEOUT)

