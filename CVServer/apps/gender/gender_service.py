# encoding=utf-8

##########
# prepare
##########
import json
from ...util.logger import Logger
from ...util import config

logger = Logger('gender_service', log2console=False, log2file=True, logfile=config.GENDER_LOG_PATH).get_logger()

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
modelDefInput = basePath + "/model/gender_deploy_correct.prototxt"
pretrainedModelInput = basePath + "/model/gender_model_correct.caffemodel"
imgPath = basePath + '/testimg'

mean = np.array([104, 117, 123])

modelClassifier = caffe.Classifier(modelDefInput, pretrainedModelInput,
                                   image_dims=[256, 256], mean=mean, raw_scale=255.0, channel_swap=(2, 1, 0))

dlib_detector = dlib.get_frontal_face_detector()

output = [
    'female',
    'male',
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
            predictionsForImage = modelClassifier.predict(face)
            # pred = predictionsForImage.reshape((len(output)))
            pred = predictionsForImage[0]
            confidence = round(pred[pred.argmax()], 4)
            res_list.append({"id": pred.argmax(), "prob": confidence})
        return (res_list, "success")


#############
# Test case
#############
imgURL = "https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg"
get_img_from_url(imgURL)

# filelists = os.listdir(imgPath)
filelists = []
print("filelists", "\n".join(filelists))
for file in filelists:
    imgFile = imgPath + '/' + file

    inputs = [caffe.io.load_image(imgFile)]

    predictionsForImage = modelClassifier.predict(inputs)
    pred = predictionsForImage.reshape((len(output)))
    predictionName = output[pred.argmax()]
    predictionConfidence = pred[pred.argmax()]

    print(file)
    print("P:", predictionName, predictionConfidence, pred.argmax())

# cv2.imshow('test',inputs[0])
# cv2.waitKey()

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
