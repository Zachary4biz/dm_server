#!/usr/bin/env bash
set -e
source ~/anaconda3/etc/profile.d/conda.sh
conda activate cv3.6
service_name=$1
if [[ ! -n "${service_name}" ]]; then
    echo ">>> 未指定服务:"
    echo " 参数             port(default)  usage"
    echo " all             |8000|        「同时」开启 [所有] 服务"
    echo "    - 补充说明：会将所有子服务和profile开在同一个端口（默认8000）下的不同路由"
    echo " seq             |*   |        「分别」开启 [所有] 服务"
    echo "    - 补充说明：依次启动子服务、profile，各有各的默认端口"
    echo " age             |8001|         开启 [年龄检测] 服务"
    echo " gender          |8002|         开启 [性别检测] 服务"
    echo " nsfw            |8003|         开启 [鉴黄] 服务"
    echo " obj             |8004|         开启 [目标检测] 服务"
    echo " cutcut_profile  |8000|         开启 [画像总成] 服务"
    exit 1
else
    echo "将启动服务: ${service_name}"
fi

localIP=`ifconfig | grep -Eo 'inet [0-9\.]+' | grep -v 127.0.0.1 | grep -Eo '[0-9\.]+' | head -1` # 类似实体机如mac有多个网口（wifi和usb网线）取第一个
if [[ ${service_name} = "seq" ]]; then
    echo "执行 seq， 依次启动各个服务: "
    for service in "age" "gender" "nsfw" "obj" "cutcut_profile"
    do
        echo "    开启 ${service}"
        python -u _start_service_separate.py --service ${service} --host ${localIP}
    done
else
    python -u _start_service_separate.py --service ${service_name} --host ${localIP}
fi

