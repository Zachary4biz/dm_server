# encoding:utf-8
# author: zac
# create-time: 2019-07-10 18:12
# usage: - 
import os
import json
import cv2
from matplotlib import pyplot as plt


# 解析文件获带json信息的图片文件
def write2file_useful_json(output_fp="/home/zhoutong/facedata/all_json_file_path.txt"):
    base_dir = "/home/zhoutong/facedata/CASIA-maxpy-clean"
    sub_dir_list = [os.path.join(base_dir, i) for i in os.listdir(base_dir)]
    res_path_list = []
    for sub_dir in sub_dir_list:
        if os.path.isdir(sub_dir):
            res_path_list.extend([os.path.join(sub_dir, i) for i in os.listdir(sub_dir) if ".json" in i])
    with open(output_fp, "w") as f:
        for p in res_path_list:
            f.writelines(p + "\n")
    return None


def process_img(img, rect_list, expand_r=0.15):
    img_list = []
    H, W, _ = img.shape
    for rect in rect_list:
        (top, left, width, height) = (rect['top'], rect['left'], rect['width'], rect['height'])
        top = int(top - expand_r * height)
        height = int((1 + expand_r * 2) * height)
        left = int(left - expand_r * width)
        width = int((1 + expand_r * 2) * width)
        top = top if top > 0 else 0
        left = left if left > 0 else 0
        img_list.append(img[top:top + height, left:left + width])
    return img_list


def prepare(json_fp):
    img_fp = os.path.splitext(json_fp)[0] + ".jpg"
    with open(json_fp, "r") as f:
        content = json.load(f)
    img = cv2.imread(img_fp)
    rect_list = [i['face_rectangle'] for i in content['faces']]
    ethnicity_list = [i['attributes']['ethnicity']['value'] for i in content['faces']]
    face_list = process_img(img, rect_list)
    return face_list, ethnicity_list


def get_new_fp(fp="/home/zhoutong/facedata/CASIA-maxpy-clean/0000133/007.json"):
    CASIA_dir, img_collection_dir = os.path.split(os.path.dirname(fp))
    f_name = img_collection_dir + "_" + os.path.basename(fp).replace("json", "jpg")
    f_dir = os.path.abspath(os.path.join(os.path.join(CASIA_dir, "../"), "prepared_data", "face_img"))
    return os.path.join(f_dir, f_name)


def show(face, eth):
    _ = plt.imshow(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
    print("ethnicity: ", eth)
    plt.show()


if __name__ == '__main__':
    # load useful json file as fp_lsit
    json_fp = "/home/zhoutong/facedata/all_json_file_path.txt"
    write2file_useful_json(json_fp)
    with open(json_fp, "r") as f:
        fp_list = [i.strip() for i in f.readlines()]

# Test
for fp in fp_list[198:199]:
    new_fp = get_new_fp(fp)
    print(fp)
    print(new_fp)
    face_list, ethnicity_list = prepare(fp)
    for face, eth in zip(face_list, ethnicity_list):
        # show(face, eth)
        cv2.imwrite(new_fp, face)
