#!/usr/bin/env bash
set -e
source ~/anaconda3/etc/profile.d/conda.sh
conda activate cv3.6
service_name=$1
if [[ ! -n "${service_name}" ]]; then
    echo ">>> 未指定服务:"
    echo " all      开启 [所有] 服务"
    echo " profile  开启 [画像总成] 服务"
    echo " age      开启 [年龄检测] 服务"
    echo " gender   开启 [性别检测] 服务"
    echo " nsfw     开启 [鉴黄] 服务"
    echo " obj      开启 [目标检测] 服务"
    exit 1
else
    echo "将启动服务: ${service_name}"
fi

python -u _start_service_separate.py service_name


