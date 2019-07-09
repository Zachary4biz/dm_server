# author: zac
# create-time: 2019-07-09 16:25
# usage: - 
import urllib
import numpy as np
import cv2

def get_img_from_url(url):
    try:
        url_response = urllib.urlopen(url)
        img_array = np.array(bytearray(url_response.read()), dtype=np.uint8)
        img = cv2.imdecode(img_array, -1)
        return img
    except Exception, e:
        print e
        return None
