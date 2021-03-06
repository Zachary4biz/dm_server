# author: zac
# create-time: 2019-12-25 16:13
# usage: - 
import json
import requests
import numpy as np
try:
    import caffe
except Exception as e:
    print(e)


class TFServingModel:
    class CustomException(Exception):
        pass

    def __init__(self, serving_url):
        self.serving_url = serving_url

    # img给imgPIL和imgArr都可以
    # np.array(ndarray) 的结果还是ndarray
    # 返回结果直接是json.loads没有用np.array()封装，因为yolo返回的是字典
    def predict(self, img):
        data = json.dumps({"signature_name": "serving_default", "instances": [np.array(img).tolist()]})
        headers = {"content-type": "application/json"}
        json_response = requests.post(self.serving_url, data=data, headers=headers)
        if json_response.status_code != 200:
            raise self.CustomException(f"request TFServing failed. status_code: {json_response.status_code} content: {json_response.text}")
        predictions = json.loads(json_response.text)["predictions"][0]
        return predictions


def load_model(prototxt_fp, caffemodel_fp, dims_inp=None, mean_inp=None, raw_scale_inp=255.0, channel_swap_inp=(2, 1, 0)):
    dims = [256, 256] if dims_inp is None else dims_inp
    mean = np.array([104, 117, 123]) if mean_inp is None else mean_inp
    return caffe.Classifier(prototxt_fp, caffemodel_fp, image_dims=dims, mean=mean, raw_scale=raw_scale_inp,
                            channel_swap=channel_swap_inp)

