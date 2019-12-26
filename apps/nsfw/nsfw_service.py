# encoding=utf-8

##########
# prepare
##########
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ['GLOG_minloglevel'] = '2'  # 控制caffe日志
from config import CONFIG_NEW
from util.cv_util import CVUtil
from django.conf import settings
from services import api_format_predict

NAME = "nsfw"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['normal pic', 'nsfw pic']
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
modelClassifier = settings.ALGO_MODEL[NAME]
load_img_func = cvUtil.img_from_url_cv2
param_check_list = ['img_url', 'id']


def get_default_res(info="default res"):
    return {'nsfw_prob': -1, 'sfw_prob': -1, 'info': info}


def _predict(img):
    try:
        img_pro = cvUtil.pre_cv2caffe(img)
        # predict是一个二维数组shape(1,2)
        # 例如: array([[0.09189981, 0.90810025]], dtype=float32)
        # 含义是: 第一项是非nsfw概率(0.09)，第二项是nsfw概率(0.908)
        pred = modelClassifier.predict(img_pro)[0]
        sfw_prob = round(float(pred[0]), 4)  # 非nsfw的概率
        nsfw_prob = round(float(pred[1]), 4)  # 为nsfw的概率
        res = {'nsfw_prob': nsfw_prob, 'sfw_prob': sfw_prob, 'info': output[int(pred.argmax())]}
        return res, "success"
    except Exception as e:
        logger.error(e)
        return None, repr(e)


def predict(request):
    return api_format_predict(request,
                              logger=logger, param_check_list=param_check_list,
                              load_img_func=load_img_func, get_default_res=get_default_res, _predict=_predict,
                              TIMEOUT=CONFIG_NEW[NAME].timeout)

