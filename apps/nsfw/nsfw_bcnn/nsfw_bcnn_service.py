# author: zac
# create-time: 2020-02-13 09:41:33
# usage: - 
import os
import sys
import time
import json
import numpy as np
from django.conf import settings
from django.http import HttpResponse
from urllib.parse import unquote
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import CONFIG_NEW # config的依赖路径在cofnig.py里已经默认添加
from util.cv_util import CVUtil
from util import common_util
from util.model_util import TFServingModel
from services import api_format_predict

NAME = "nsfw_bcnn"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['normal pic', 'nsfw pic']
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
modelClassifier: TFServingModel = settings.ALGO_MODEL[NAME]
load_img_func = cvUtil.img_from_url_PIL
param_check_list = ['img_url', 'id']
IMAGE_SHAPE=(224,224)

def get_default_res(info="default res"):
    return [{'nsfw_prob': -1, 'sfw_prob': -1, 'info': info}]


def _predict(imgPIL):
    try:
        # tfserving的模型是 ['NSFW','SFW'] 和这里不一致，手动调换一下
        imgArr = np.array(imgPIL.resize(IMAGE_SHAPE))/255
        pred = modelClassifier.predict(imgArr)[::-1]
        pred = np.array(pred)
        sfw_prob = round(float(pred[0]), 4)  # 非nsfw的概率
        nsfw_prob = round(float(pred[1]), 4)  # 为nsfw的概率
        res_list = {
            "nsfw_prob": nsfw_prob,
            "sfw_prob": sfw_prob,
            "info": output[int(pred.argmax())]
            }
        return res_list, "success"
    except TFServingModel.CustomException as e:
        logger.error(e)
        return None, "TFServing Model Failed"
    except Exception as e:
        logger.error(e)
        return None, repr(e)


def predict(request):
    return api_format_predict(request,
                              logger=logger, param_check_list=param_check_list,
                              load_img_func=load_img_func, get_default_res=get_default_res, _predict=_predict,
                              TIMEOUT=CONFIG_NEW[NAME].timeout)


