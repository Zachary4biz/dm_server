# author: zac
# create-time: 2019-12-18 12:47
# usage: -
import os
import tensorflow as tf


class EthnicityM:
    _defualts={
        "model_path": os.path.dirname(__file__)+'/model/inception_v3_pb',
    }

    def __init__(self, model_path=_defualts['model_path']):
        self.model = tf.keras.models.load_model(model_path)

    def predict_batch(self, inp):
        return self.model.predict(inp)
