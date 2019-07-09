# encoding=utf-8

##########
# prepare
##########
import json
from ...util.logger import Logger
from ...util import config

logger = Logger('age_service', log2console=False, log2file=True, logfile=config.AGE_LOG_PATH).get_logger()

#########
# cv part
#########
import sys
import caffe
import numpy as np
import cv2
import urllib
import dlib
import os

print("文件路径:", os.path.dirname(__file__))
basePath = os.path.dirname(__file__)
modelDefInput = basePath + "/model/full_age.prototxt"
pretrainedModelInput = basePath + "/model/full_age.caffemodel"
imgPath = basePath + '/testimg'

mean = np.array([104, 117, 123])

modelClassifier = caffe.Classifier(modelDefInput, pretrainedModelInput,
                                   image_dims=[256, 256], mean=mean, raw_scale=255.0, channel_swap=(2, 1, 0))

dlib_detector = dlib.get_frontal_face_detector()

output = [
    '71+ years',
    '36 - 50 years',
    '51 - 70 years',
    '6 - 15 years',
    '0 - 5 years',
    '16 - 25 years',
    '26 - 35 years'
]


def get_face_list(img, enlarge=0.2):
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    rect_list = dlib_detector(gray_img, 1)
    face_img_list = []
    for rect in rect_list:
        (h, w) = (rect.height(), rect.width())
        (h, w) = (int(h * enlarge), int(w * enlarge))
        top = rect.top() - h if rect.top() - h > 0 else 0
        bottom = rect.bottom() + h if rect.bottom() + h < img.shape[0] else img.shape[0]
        left = rect.left() - h if rect.left() - h > 0 else 0
        right = rect.right() + h if rect.right() + h < img.shape[1] else img.shape[1]
        face_img_list.append(img[top:bottom, left:right])
    return face_img_list


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
    face_list = get_face_list(img)
    if len(face_list) == 0:
        return (None, "no frontal-face detected.")
    else:
        face_list = [pre_process_img(i) for i in face_list]
        res_list = []
        for face in face_list:
            pred = modelClassifier.predict(face)[0]
            confidence = round(pred[pred.argmax()], 4)
            res_list.append({"id": pred.argmax(), "prob": confidence})
        return (res_list, "success")


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

imgURL = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg"
_predict(get_img_from_url(imgURL))

#################
# Django API part
#################
from django.http import HttpResponse


def predict(request):
    params = request.GET
    if 'img_url' in params and 'id' in params:
        img = get_img_from_url(params['img_url'])
        if img is None:
            json_str = json.dumps({"result": [{'id': -1, 'prob': 1.0, 'info': 'load image fail'}]})
            logger.error("at [id]: {} load img fail [ur]: {}".format(params['id'], params['img_url']))
        else:
            (res_list, remark) = _predict(img)
            if (res_list is None):
                json_str = json.dumps({"result": [{'id': -1, 'prob': 1.0, 'info': remark}]})
                logger.warn("at [id]: {} [res]: {} [remark]: {}".format(params['id'], json_str, remark))
            else:
                [d.update({"info": output[d['id']]}) for d in res_list]
                json_str = json.dumps({"result": res_list})
                logger.info("at [id]: {} [res]: {}".format(params['id'], json_str))
        return HttpResponse(json_str, status=200)
    else:
        return HttpResponse("use GET, param: 'img_url', 'id'", status=400)
