#!/usr/bin/env bash
set -e
source ~/anaconda3/etc/profile.d/conda.sh
conda activate cv3.6

service_name=$1
if [[ ! -n "${service_name}" ]]; then
    echo ">>> 未指定服务"
    echo " all      关闭 [所有] 服务"
    echo " cutcut_profile  关闭 [画像总成] 服务"
    echo " age      关闭 [年龄检测] 服务"
    echo " gender   关闭 [性别检测] 服务"
    echo " nsfw     关闭 [鉴黄] 服务"
    echo " obj      关闭 [目标检测] 服务"
    exit 1
else
    echo "将kill服务: ${service_name}"
fi

python -u _stop_service.py ${service_name}

echo "remaining as follow:"
ps -ef | grep "cutcut"
