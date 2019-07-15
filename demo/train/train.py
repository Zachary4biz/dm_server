# encoding:utf-8
"""
在gpu服务器上训练模型
"""

import numpy as np
import os
import tensorflow as tf

import mobilenet_v2

import cv2
import math
import json
import pandas as pd
import random

IMG_WIDTH = 128
IMG_HEIGHT = 128
IMAGE_WIDTH = IMG_WIDTH
IMAGE_HEIGHT = IMG_HEIGHT
IMG_CHANNEL = 3
shuffle = True
CHECKPOINTS_DIR = 'my106/'

BATCH_SIZE = 20
NUM_EPOCHS = 40000000000

global modelValLoss
global totalValLoss
global valIter
valIter = 0

initialLearningRate = 0.001
learningRateDecay = 0.0000001
weightDecay = 0.0005
numPoints = 106  # 68
numPointsX2 = numPoints * 2
print(numPoints, numPointsX2)

train_input_name = 'data_train_casia.csv'
test_input_name = 'data_test_casia.csv'


# Randomly crop the image to a specific size. For data augmentation
def random_crop(image, label, crop_height, crop_width):
    if (image.shape[0] != label.shape[0]) or (image.shape[1] != label.shape[1]):
        raise Exception('Image and label must have the same dimensions!')

    if (crop_width <= image.shape[1]) and (crop_height <= image.shape[0]):
        x = random.randint(0, image.shape[1] - crop_width)
        y = random.randint(0, image.shape[0] - crop_height)

        if len(label.shape) == 3:
            return image[y:y + crop_height, x:x + crop_width, :], label[y:y + crop_height, x:x + crop_width, :]
        else:
            return image[y:y + crop_height, x:x + crop_width, :], label[y:y + crop_height, x:x + crop_width]
    else:
        raise Exception('Crop shape (%d, %d) exceeds image dimensions (%d, %d)!' % (
        crop_height, crop_width, image.shape[0], image.shape[1]))


def data_augmentation(input_image, output_image):
    # Data augmentation
    h, w = input_image.shape[0], input_image.shape[1]
    argsrotation = 20.0

    randcrop = random.uniform(0.8, 1)
    #     print(randcrop)
    crop_width = (int)(randcrop * w)
    crop_height = (int)(randcrop * h)
    # input_image, output_image = random_crop(input_image, output_image, args.crop_height, args.crop_width)#utils.
    input_image, output_image = random_crop(input_image, output_image, crop_height, crop_width)

    if random.randint(0, 1):  # args.h_flip and
        #         print('h_flip')
        input_image = cv2.flip(input_image, 1)
        output_image = cv2.flip(output_image, 1)
    if random.randint(0, 1):  # args.rotation:
        #         print('rotation')
        angle = random.uniform(-1 * argsrotation, argsrotation)
        # if random.randint(0,1):#args.rotation:
        # print('rotation')
        M = cv2.getRotationMatrix2D((input_image.shape[1] // 2, input_image.shape[0] // 2), angle, 1.0)
        input_image = cv2.warpAffine(input_image, M, (input_image.shape[1], input_image.shape[0]),
                                     flags=cv2.INTER_NEAREST)
        output_image = cv2.warpAffine(output_image, M, (output_image.shape[1], output_image.shape[0]),
                                      flags=cv2.INTER_NEAREST)

    return input_image, output_image


def smooth_l1_loss(bbox_prediction, bbox_target, sigma=1.0):
    """
    Return Smooth L1 Loss for bounding box prediction.

    Args:
        bbox_prediction: shape (1, H, W, num_anchors * 4)
        bbox_target:     shape (1, H, W, num_anchors * 4)


    Smooth L1 loss is defined as:

    0.5 * x^2                  if |x| < d
    abs(x) - 0.5               if |x| >= d

    Where d = 1 and x = prediction - target

    """
    #     sigma2 = sigma ** 2
    #     diff = bbox_prediction - bbox_target
    #     abs_diff = tf.abs(diff)
    #     abs_diff_lt_sigma2 = tf.less(abs_diff, 1.0 / sigma2)
    #     bbox_loss = tf.reduce_sum(
    #         tf.where(
    #             abs_diff_lt_sigma2, 0.5 * tf.square(abs_diff),
    #             abs_diff - 0.5
    #         ), [1]
    #     )
    #     return bbox_loss

    x = bbox_prediction - bbox_target
    l2 = 0.5 * (x ** 2.0)
    l1 = tf.abs(x) - 0.5

    condition = tf.less(tf.abs(x), 1.0)
    re = tf.where(condition, l2, l1)

    loss = tf.reduce_sum(re)

    return loss


def wing_loss(landmarks, labels, w=10.0, epsilon=2.0):
    """
    Arguments:
        landmarks, labels: float tensors with shape [batch_size, num_landmarks, 2].
        w, epsilon: a float numbers.
    Returns:
        a float tensor with shape [].
    """
    #     batch_size=landmarks.shape[0]#tf.getshape(landmarks)[0]

    #     landmarks = np.reshape(landmarks, (-1, 2))
    #     labels = np.reshape(labels, (-1, 2))
    #     with tf.name_scope('wing_loss'):
    print(landmarks.shape)
    print(labels.shape)

    x = landmarks - labels
    c = w * (1.0 - math.log(1.0 + w / epsilon))
    absolute_x = tf.abs(x)
    losses = tf.where(
        tf.greater(w, absolute_x),
        w * tf.log(1.0 + absolute_x / epsilon),
        absolute_x - c
    )
    loss = tf.reduce_mean(tf.reduce_sum(losses, axis=[1, 2]), axis=0, name='loss')
    #     loss = tf.reduce_mean(tf.reduce_sum(losses, axis=[1]), axis=0, name='loss')
    return loss


def readImageNames(csv_input):
    examples = pd.read_csv(csv_input)
    imageNames = []
    for _, row in examples.iterrows():
        linedata = row
        imname, jsonname = linedata['jpg'], linedata['json']
        imageNames.append((imname, jsonname))

    random.shuffle(imageNames)
    return imageNames


##########################################################################################

def performValidation(sess, k):
    # calculate validation loss first
    i = 0
    batchCounter = 0
    totalValLoss = 0

    global modelValLoss

    while i < len(valImageNames):
        batchValImages = []
        batchValLabels = []

        j = i
        while j < i + BATCH_SIZE and j < len(valImageNames):
            #             print(j, BATCH_SIZE)
            valImage = cv2.imread(valImageNames[j][0])
            if valImage is None:
                continue

            jsonname = valImageNames[j][1]
            with open(jsonname, 'r') as json_file:
                points = json.load(json_file)

            if len(points) < numPoints:  # why some label is not loaded
                print(jsonname)
                continue

            if valImage.shape[0] != IMAGE_HEIGHT or valImage.shape[1] != IMAGE_WIDTH:
                valImage = cv2.resize(valImage, (IMAGE_WIDTH, IMAGE_HEIGHT))
            #                 print(valImage.shape)
            #                 print('the shape is not correct????')
            #                 raw_input()

            valImage = valImage.astype("float32")
            valImage = valImage / 255.0
            #             points = np.reshape(points, (-1, 2))

            batchValLabels.append(points)
            batchValImages.append(valImage)
            j = j + 1

        loss = sess.run(["loss:0"], feed_dict={
            "input_to_float:0": batchValImages,
            "inptrue:0": batchValLabels,
            "global_step:0": batchCounter,
        })

        loss = loss[0] / float(len(batchValImages))

        totalValLoss += loss
        batchCounter += 1
        i = i + BATCH_SIZE

    print "Test iteration - ", k
    print "Check the total validation loss - ", totalValLoss / float(batchCounter)
    if (k == 0):
        modelValLoss = totalValLoss
        saver.save(sess, CHECKPOINTS_DIR + "enetperson-" + str(k) + ".ckpt")
        print('---------------------------------------------')
        print "Saving the model"
    else:
        if (totalValLoss < modelValLoss):
            modelValLoss = totalValLoss
            saver.save(sess, CHECKPOINTS_DIR + "enetperson-" + str(k) + ".ckpt")
            print('---------------------------------------------')
            print "Saving the model"


def trainEpoch(sess):
    i = 0

    global valIter

    batchCounter = 0
    if shuffle:
        random.shuffle(trainImageNames)

    while i < len(trainImageNames):
        batchTrainImages = []
        batchTrainLabels = []

        j = i
        while j < i + BATCH_SIZE and j < len(trainImageNames):
            #             print(j, BATCH_SIZE)
            trainImage = cv2.imread(trainImageNames[j][0])
            if trainImage is None:
                continue

            jsonname = trainImageNames[j][1]
            with open(jsonname, 'r') as json_file:
                points = json.load(json_file)

            if len(points) < numPoints:  # why some label is not loaded
                print(jsonname)
                continue

            print(j, trainImageNames[j][0])

            if trainImage.shape[0] != IMAGE_HEIGHT or trainImage.shape[1] != IMAGE_WIDTH:
                trainImage = cv2.resize(trainImage, (IMAGE_WIDTH, IMAGE_HEIGHT))
            #                 print(trainImage.shape)
            #                 print('the shape is not correct????')
            #                 raw_input()

            trainImage = trainImage.astype("float32")
            trainImage = trainImage / 255.0
            #             points = np.reshape(points, (-1, 2))

            #             print(trainImage.shape)
            #             print(len(points))

            batchTrainImages.append(trainImage)
            batchTrainLabels.append(points)
            j = j + 1

        loss, _ = sess.run(["loss:0", "trainop"], feed_dict={
            "input_to_float:0": batchTrainImages,
            "inptrue:0": batchTrainLabels,
            "global_step:0": batchCounter,
        })
        print "Check the train loss after batch - ", batchCounter
        print loss.shape
        print loss / float(len(batchTrainImages))
        batchCounter += 1
        i = i + BATCH_SIZE


##########################################################################################

#             bbox = myBoxProcess.obtain_bbox(bbox, input_width*1.0/input_height)
#             bbox = myBoxProcess.pad_bbox(bbox, pad_ratio=0.05)

#             cropImg, pad, offset, scale = myBoxProcess.preprocess(im, bbox, input_width, input_height)
#             # print(pad, offset, scale)

#             if cropImg.shape[0] < 1 or cropImg.shape[1] < 1:
#                 print(bbox)
#                 # raw_input()
#                 continue

#             if cropImg.shape[0] != input_height or cropImg.shape[1] != input_width:
#                 print(cropImg.shape)
#                 cropImg = cv2.resize(cropImg, (input_width, input_height))

#             points_normalized = get_valid_points(bbox, points)
##########################################################################################
trainImageNames = readImageNames(train_input_name)
valImageNames = readImageNames(test_input_name)
# print(trainImageNames[0])
print(len(trainImageNames))

inputs = tf.placeholder("float32", [None, IMG_HEIGHT, IMG_WIDTH, 3], name="input_to_float")
inptrue = tf.placeholder("float32", [None, numPointsX2], name="inptrue")
global_step = tf.placeholder("int32", name="global_step")

# logits, pred = mobilenet_v2.mobilenetv2_caffe(inputs, numPointsX2)
logits, pred = mobilenet_v2.mobilenetv2_caffe(inputs, 4)
[0.134,0.34426,0.77456,0.23523], 0.78

# landmarks = tf.reshape(inptrue, (-1, numPoints, 2))
# logits2 = tf.reshape(logits, (-1, numPoints, 2))
# loss = wing_loss(landmarks, logits2)
loss=tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(labels=inptrue,logits=logits),name='loss')

learningRate = tf.train.inverse_time_decay(initialLearningRate, global_step, 1, learningRateDecay, name="ratedecay")
optimizer = tf.train.AdamOptimizer(learningRate, name="adamfull")
train_op = optimizer.minimize(loss, name="trainop")

config = tf.ConfigProto()
config.gpu_options.allow_growth = True

with tf.Session(config=config) as sess:
    saver = tf.train.Saver(max_to_keep=20)

    sess.run([tf.global_variables_initializer(), tf.local_variables_initializer()])

    if not os.path.exists(CHECKPOINTS_DIR):
        os.makedirs(CHECKPOINTS_DIR)
    else:
        ckpt_path = tf.train.latest_checkpoint(CHECKPOINTS_DIR)
        print(ckpt_path)
        if not ckpt_path is None:
            print('restore the last training', ckpt_path)
            saver.restore(sess, ckpt_path)
        else:
            print('no restore this time', ckpt_path)

    print('----------------------begin trainng...---------------------------------------')
    k = 0
    writer = tf.summary.FileWriter(CHECKPOINTS_DIR, sess.graph)
    while k < NUM_EPOCHS:
        # start training
        print "Starting training"
        trainEpoch(sess)
        performValidation(sess, k)
        print "Epoch training complete ", k
        k = k + 1

