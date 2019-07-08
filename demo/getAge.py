import sys
import caffe
import numpy as np
# import Image
import os
# import json
# from shutil import copyfile
# from sklearn.metrics import confusion_matrix as cm, classification_report as cr
import cv2

modelDefInput = "model/full_age.prototxt"
pretrainedModelInput = "model/full_age.caffemodel"
meanFileInput = "model/googlenetmeanbgr.npy"
# imgFile = 'testimg/Aaron_Eckhart_0001.bmp'
imgPath = 'testimg'
# imgPath = '/mnt/shared/libcaffe2/shenhe/group/0'

mean = np.load(meanFileInput)
mean = mean[:,:227,:227]

modelClassifier = caffe.Classifier(modelDefInput, pretrainedModelInput,
            image_dims=[256,256], mean=mean, raw_scale=255.0, channel_swap=(2,1,0))

# modelNamesFile = [
# "/6", #0
# "/4", #1
# "/5", #2
# "/1", #3
# "/0", #4
# "/2", #5
# "/3", #6
# ]

modelNamesFile = [
'71+ years',
'36 - 50 years',
'51 - 70 years',
'6 - 15 years',
'0 - 5 years',
'16 - 25 years',
'26 - 35 years'
]

# 0 - 5 years  
# 6 - 15 years
# 16 - 25 years
# 26 - 35 years
# 36 - 50 years
# 51 - 70 years
# 71+ years

filelists = os.listdir(imgPath)

for file in filelists:
    imgFile = imgPath + '/' + file

    inputs = [caffe.io.load_image(imgFile)]
            
    predictionsForImage = modelClassifier.predict(inputs)
    pred = predictionsForImage.reshape((len(modelNamesFile)))
    predictionName = modelNamesFile[pred.argmax()]
    predictionConfidence = pred[pred.argmax()]

    print(file)
    print("P:", predictionName, predictionConfidence, pred.argmax())

    cv2.imshow('test',inputs[0])
    cv2.waitKey()
