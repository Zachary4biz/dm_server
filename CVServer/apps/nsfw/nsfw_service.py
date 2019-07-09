# encoding=utf-8

##########
# prepare
##########
import json
from ...util.logger import Logger
from ...util import config
from ...util import common_util

logger = Logger('nsfw_service', log2console=False, log2file=True, logfile=config.NSFW_LOG_PATH).get_logger()

#########
# cv part
#########
import sys
import caffe
import numpy as np
import os
import cv2
import urllib
import dlib

print("文件路径:", os.path.dirname(__file__))
basePath = os.path.dirname(__file__)
modelDefInput = basePath + "/model/nsfw_deploy.prototxt"
pretrainedModelInput = basePath + "/model/resnet_50_1by2_nsfw.caffemodel"
meanFileInput = basePath + "/model/googlenetmeanbgr.npy"
imgPath = basePath + '/testimg'

mean = np.array([104, 117, 123])

modelClassifier = caffe.Classifier(modelDefInput, pretrainedModelInput,
                                   image_dims=[256, 256], mean=mean, raw_scale=255.0, channel_swap=(2, 1, 0))

output = [
    'normal pic',
    'nsfw pic'
]


def pre_process_img(img, img_height=256, img_width=256):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img / 255.0
    return [img]


def get_img_from_url(url):
    try:
        url_response = urllib.urlopen(url)
        img_array = np.array(bytearray(url_response.read()), dtype=np.uint8)
        img = cv2.imdecode(img_array, -1)
        return img
    except Exception, e:
        print e
        return None


def _predict(img):
    img_pro = pre_process_img(img)
    pred = modelClassifier.predict(img_pro)[0]
    confidence = round(pred[pred.argmax()], 4)
    return {"id": pred.argmax(), "prob": confidence}


#############
# Test case
#############
imgURL = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg"
_predict(get_img_from_url(imgURL))

#################
# Django API part
#################
from django.http import HttpResponse


def predict(request):
    params = request.GET
    if 'img_url' in params and 'id' in params:
        img, delta_t = common_util.timeit(get_img_from_url, params['img_url'])
        logger.debug("load img: [url]: {} [elapsed]: {}".format(params['img_url'], delta_t))
        if img is None:
            logger.error("at [id]: {} load img fail from [ur]: {}".format(params['id'], params['img_url']))
        else:
            res = _predict(img)
            res.update({"info": output[res['id']]})
            json_str = json.dumps({"result": res})
            return HttpResponse(json_str, status=200)
    else:
        return HttpResponse("use GET, param: 'img_url', 'id'", status=400)
