import sys
import caffe
import numpy as np
# import Image
import os
import cv2

modelDefInput = "model/gender_deploy_correct.prototxt"
pretrainedModelInput = "model/gender_model_correct.caffemodel"
meanFileInput = "model/googlenetmeanbgr.npy"
# imgFile = 'testimg/Aaron_Eckhart_0001.bmp'
# imgPath = 'testimg'
imgPath = '/mnt/shared/libcaffe2/shenhe/group/2'

mean = np.load(meanFileInput)
mean = mean[:, :227, :227]
print(mean)

modelClassifier = caffe.Classifier(modelDefInput, pretrainedModelInput,
                                   image_dims=[256, 256], mean=mean, raw_scale=255.0, channel_swap=(2, 1, 0))

modelNamesFile = [
    'female',
    'male',
]

filelists = os.listdir(imgPath)

for file in filelists:
    imgFile = imgPath + '/' + file

    if 1:
        image1 = cv2.imread(imgFile)
        image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
        image1 = image1 / 255.
        inputs = [image1]
    else:
        inputs = [caffe.io.load_image(imgFile)]
    # print(inputs)

    predictionsForImage = modelClassifier.predict(inputs)
    pred = predictionsForImage.reshape((len(modelNamesFile)))
    predictionName = modelNamesFile[pred.argmax()]
    predictionConfidence = pred[pred.argmax()]

    print(file)
    print("P:", predictionName, predictionConfidence, pred.argmax())

    cv2.imshow('test', inputs[0])
    cv2.waitKey()

# import os
# os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   # see issue #152
# os.environ["CUDA_VISIBLE_DEVICES"]="0"


# from __future__ import absolute_import
# from __future__ import division
# from __future__ import print_function

# import argparse
# import sys

# import tensorflow as tf
# import numpy as np
# from scipy import misc

# # import caffe
# import cv2


# print('loc here')

# pb_file = 'curpb.pb' 

# # np.set_printoptions(threshold=np.inf)
# # np.set_printoptions(suppress=True)

# print("one")

# # sess = tf.Session()
# sess = tf.InteractiveSession()
# graph = sess.graph

# print("two")


# graph_def = tf.GraphDef()
# with tf.gfile.GFile(pb_file, "rb") as f:
# 	graph_def.ParseFromString(f.read())
# #with tf.Graph().as_default() as graph:
# # fix nodes
# for node in graph_def.node:
# #     print(node.op)
#     if node.op == 'RefSwitch':
#         node.op = 'Switch'
#         for index in xrange(len(node.input)):
#             if 'moving_' in node.input[index]:
#                 node.input[index] = node.input[index] + '/read'
#     elif node.op == 'AssignSub':
#         node.op = 'Sub'
#         if 'use_locking' in node.attr: del node.attr['use_locking']

# with graph.as_default():
# 	tf.import_graph_def(graph_def, name="")
# 	graph_nodes=[n for n in graph_def.node]#tzg

# print('done1')


# %matplotlib inline
# from matplotlib import pyplot as plt
# from IPython.display import clear_output

# folderID = 4
# candidateFolder = ["../../../ICNet/my_clothing_parsing/", 
#                    "../../../ICNet/wholeperson-256/", 
#                    "../../../ICNet/jp/", 
#                    "../../../ICNet/testimgs/",
#                   "../../../ICNet/mask_chang/segperson__ds1/img/"   ##4
#                   ]
# sourceFolder = candidateFolder[folderID]
# if 1:
#     sourceFolder = "../../../ICNet/my_clothing_parsing/"
# else:
#     sourceFolder = "../../../ICNet/wholeperson-256/"

# interFolder = "result/"

# if not os.path.exists(interFolder):
#     os.makedirs(interFolder)

# enetgraph = graph
# enetmodel = enetgraph.get_tensor_by_name("finalact/activationfinal:0")

# for file in os.listdir(sourceFolder):
#     print(file)

#     trainImage1 = cv2.imread(sourceFolder + file)
#     trainImage1 = cv2.resize(trainImage1, (IMAGE_WIDTH, IMAGE_HEIGHT))
#     image = trainImage1.copy()
#     trainImage1 = trainImage1.astype("float32")
#     # normalize the image
#     trainImage1 = trainImage1/255.0
#     trainImages = []
#     trainImages.append(trainImage1)

#     print("three")


#     answer1 = sess.run(["finalact/activationfinal:0"], feed_dict={"inp:0":np.array(trainImages),
#                                               "dropout_rate1:0":1.0,
#                                               "dropout_rate2:0":1.0,
#                                               "istrain:0":False,})

#     print("five")

#     answer = answer1[0][0]
#     maxes = np.argmax(answer, axis=1)
#     oneMask = np.zeros(maxes.shape)
#     oneMask[np.where(maxes==1)] = 255
#     oneMask = np.reshape(oneMask, (IMAGE_HEIGHT,IMAGE_WIDTH))

#     mask = oneMask/255.0

#     r = image[:,:,0]
#     g = image[:,:,1]
#     b = image[:,:,2]
#     b[:] = 255
#     rn = r*mask
#     gn = g*mask
#     bn = b*mask
#     disp = cv2.merge([bn,gn,rn])#mask*255
#     disp = disp.astype(np.uint8)
#     img2 = disp[:,::-1] 
#     plt.imshow(img2)
#     plt.show()
#     raw_input()
#     clear_output()#from IPython.display import clear_output
#     fileName = file[:-4]
#     print(fileName)
