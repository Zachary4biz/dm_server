# author: zac
# create-time: 2019-11-06 19:44
# usage: -

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from django.conf import settings
from config import CONFIG_NEW
from util.cv_util import CVUtil
from util.model_util import TFServingModel
from services import api_format_predict

NAME = "vectorize"
TIMEOUT = CONFIG_NEW[NAME].timeout
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
modelClassifier: TFServingModel = settings.ALGO_MODEL[NAME]
load_img_func = cvUtil.img_from_url_PIL
param_check_list = ['img_url', 'id']


def get_default_res(info="default res"):
    return {'vector': [], 'info': info}


def _predict(imgPIL):
    try:
        pred = np.array(modelClassifier.predict(imgPIL)[0])
        res = {'vector': pred, 'info': "success"}
        return res, "success"
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
