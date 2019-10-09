#!/usr/bin/env bash
set -e
source ~/anaconda3/etc/profile.d/conda.sh
conda activate cv3.6

service_name=$1
if [[ ! -n "${service_name}" ]]; then
    echo ">>> 未指定服务:"
    echo " 参数             port(default)  usage"
    echo " all             |*   |         关闭 [所有] 服务"
    echo " age             |8001|         关闭 [年龄检测] 服务"
    echo " gender          |8002|         关闭 [性别检测] 服务"
    echo " nsfw            |8003|         关闭 [鉴黄] 服务"
    echo " obj             |8004|         关闭 [目标检测] 服务"
    echo " cutcut_profile  |8000|         关闭 [画像总成] 服务"
    exit 1
else
    echo "将kill服务: ${service_name}"
fi

python -u _stop_service.py ${service_name}

echo "remaining as follow:"
ps -ef | grep "cutcut"