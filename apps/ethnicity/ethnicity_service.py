# author: zac
# create-time: 2019-12-18 12:19
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
from config import CONFIG_NEW
from util.cv_util import CVUtil
from util import common_util
from util.model_util import TFServingModel
from services import api_format_predict

NAME = "ethnicity"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['Caucasoid', 'Mongoloid', 'Indian', 'Negroid']
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
modelClassifier: TFServingModel = settings.ALGO_MODEL[NAME]
load_img_func = cvUtil.img_from_url_PIL
param_check_list = ['img_url', 'id']


def get_default_res(info="default res"):
    return [{'id': -1, 'prob': 1.0, 'info': info}]


def _predict(imgPIL):
    try:
        faceArr, delta_t = common_util.timeit(cvUtil.get_face_list_from_pil, imgPIL=imgPIL, enlarge=0.2, target_size=(224, 224))
        faceArr = faceArr/255
        logger.debug("[elapsed-dlib face]:{}".format(delta_t))
        if len(faceArr) == 0:
            return None, "no frontal-face detected."
        else:
            pred_list = [modelClassifier.predict(face) for face in faceArr]
            res_list = [{"id": int(pred.argmax()), "prob": round(float(pred.max()), 4), "info": output[int(pred.argmax())]} for pred in pred_list]
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


