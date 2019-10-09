# encoding=utf-8

##########
# prepare
##########
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import os
os.environ['GLOG_minloglevel'] = '2'
from config import CONFIG_NEW
from util.logger import Logger
from util import common_util
from util.cv_util import CVUtil

NAME = "gender"
TIMEOUT = CONFIG_NEW[NAME].timeout
output = ['female', 'male']
cvUtil = CVUtil()


logger = None
def get_logger():
    global logger
    if logger is None:
        logger = Logger(loggername=NAME, log2console=False, log2file=True, logfile=CONFIG_NEW[NAME].service_logfile).get_logger()
    return logger


modelClassifier = None
def get_clf():
    global modelClassifier
    if modelClassifier is None:
        basePath = os.path.dirname(__file__)
        get_logger().info(">>> loading clf (should be init) at [pid]: {} [ppid]: {}".format(os.getpid(), os.getppid()))
        modelClassifier = cvUtil.load_model(prototxt_fp=basePath + "/model/gender_deploy_correct.prototxt",
                                            caffemodel_fp=basePath + "/model/gender_model_correct.caffemodel")
    return modelClassifier


def get_default_res(info="default res"):
    return [{'id': -1, 'prob': 1.0, 'info': info}]


# 专用于predict切分人脸后的图像(caffe io下的格式)
def _predict_face_caffe_img(face):
    pred = get_clf().predict(face)[0]
    confidence = round(float(pred[pred.argmax()]), 4)
    return {"id": int(pred.argmax()), "prob": confidence}


def _predict(img):
    face_list, delta_t = common_util.timeit(cvUtil.get_face_list, img)
    get_logger().debug("[elapsed-dlib face]:{}".format(delta_t))
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
        img, delta_t = common_util.timeit(cvUtil.img_from_url_cv2, params['img_url'])
        get_logger().debug("[elapsed-load img]: {} [url]: {}".format(params['img_url'], delta_t))
        if img is None:
            # 图片加载失败
            json_str = json.dumps({"result": get_default_res(info="load img fail")})
            get_logger().error("at [id]: {} load img fail [ur]: {}".format(params['id'], params['img_url']))
        else:
            # 图片加载完毕
            (res_list, remark) = _predict(img)
            if res_list is None:
                # predict失败
                json_str = json.dumps({"result": get_default_res(info=remark)})
                get_logger().warn("at [id]: {} [res]: {} [remark]: {}".format(params['id'], json_str, remark))
            else:
                # 正常返回
                [d.update({"info": output[d['id']]}) for d in res_list]
                json_str = json.dumps({"result": res_list})
                get_logger().info("at [id]: {} [res]: {}".format(params['id'], json_str))
        get_logger().info(
            u"[id]: {} [img_url]: {} [res]: {} [elapsed-total]: {:.2f}ms [elapsed-load img]: {}ms".format(params['id'], params['img_url'], json_str,
                                                                       (time.time() - begin) * 1000, delta_t))
        return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse("use GET, param: '{}'".format(",".join(param_check_list)), status=400)


# 如果不使用懒加载就直接在此module里初始化
# if not CONFIG_NEW[NAME].use_lazy:
#     _ = get_clf()
#     _ = get_logger()
