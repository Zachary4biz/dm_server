# author: zac
# create-time: 2019-07-09 16:25
# usage: - 
import urllib
import numpy as np
import cv2
import os
os.environ['GLOG_minloglevel'] = '2'
from PIL import Image
import caffe
import dlib


class CVUtil():
    def __init__(self):
        self.dlib_detector = dlib.get_frontal_face_detector()

    @staticmethod
    def load_model(prototxt_fp, caffemodel_fp, dims_inp=None, mean_inp=None, raw_scale_inp=255.0,
                   channel_swap_inp=(2, 1, 0)):
        dims = [256, 256] if dims_inp is None else dims_inp
        mean = np.array([104, 117, 123]) if mean_inp is None else mean_inp
        return caffe.Classifier(prototxt_fp, caffemodel_fp, image_dims=dims, mean=mean, raw_scale=raw_scale_inp,
                                channel_swap=channel_swap_inp)

    @staticmethod
    def img_from_url_cv2(url):
        try:
            url_response = urllib.urlopen(url)
            img_array = np.array(bytearray(url_response.read()), dtype=np.uint8)
            img = cv2.imdecode(img_array, -1)
            return img
        except Exception, e:
            print e
            return None

    @staticmethod
    def img_from_url_PIL(url, img_size=(416,416)):
        image = CVUtil.img_from_url_cv2(url)  # 402,600,3
        image = cv2.cvtColor(cv2.resize(image, img_size), cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        return image

    @staticmethod
    def img_from_fp_caffe(file_path):
        return [caffe.io.load_image(file_path)]

    @staticmethod
    def pre_cv2caffe(img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img / 255.0
        return [img]

    def get_face_list(self, img, enlarge=0.2):
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        rect_list = self.dlib_detector(gray_img, 1)
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
