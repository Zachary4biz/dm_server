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

NAME = "nsfw_obj"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['penis','vagina','breast'] #['normal pic', 'nsfw pic']
cvUtil = CVUtil()
logger = settings.LOGGER[NAME]
modelClassifier: TFServingModel = settings.ALGO_MODEL[NAME]
load_img_func = cvUtil.img_from_url_PIL
param_check_list = ['img_url', 'id']
IMAGE_SHAPE=(416,416)
obj_class_names=output
obj_prob_hold=0.3 # 物体检测的阈值

def get_default_res(info="default res"):
    return []


def _predict(imgPIL):
    try:
        imgArr = np.array(imgPIL.resize(IMAGE_SHAPE))/255
        # 注：这里modelClassifier已经取了tfserving结果的第0项，同时这也意味着只支持每次预测一个图片
        pred = modelClassifier.predict(imgArr)
        # obj的返回结果有些特殊 逐个取
        # boxes=pred['yolo_nms']
        # probs=pred['yolo_nms_1']
        # classes=pred['yolo_nms_2']
        # num=pred['yolo_nms_3']
        kv_sorted=sorted([(k,v) for k,v in pred.items()],key=lambda x:x[0])
        boxes,probs,classes,num=[v for k,v in kv_sorted]
        # 检测到的所有物体
        label_prob_list=[(int(classes[i]),probs[i]) for i in range(num)]
        # 物体检测针对的是裸露器官，加上0.3在目标检测中就算是可靠阈值
        # 所以实际作为鉴黄分数和bcnn一起使用的时候要加倍或者其他放大方式 | 这个在nsfw_ensemble里实现
        label_prob_list=[(label,prob) for label,prob in label_prob_list if prob>=obj_prob_hold]
        res = [{"label":l,"prob":p,"name":output[l]} for l,p in label_prob_list]
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


