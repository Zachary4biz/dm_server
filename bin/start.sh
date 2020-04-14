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
    echo " vectorize       |8005|         开启 [图片向量化] 服务"
    echo "    - 补充说明：profile服务不会请求vectorize服务"
    echo " ethnicity       |8006|         开启 [人种分类] 服务"
    echo " nsfw_obj        |8007|         开启 [鉴黄obj] 服务"
    echo " nsfw_bcnn       |8008|         开启 [鉴黄bcnn] 服务"
    echo " nsfw_ensemble   |8009|         开启 [鉴黄总承] 服务"
    echo " nonage          |8010|         开启 [未成年人检测] 服务"
    echo " cutcut_profile  |8000|         开启 [画像总承] 服务"
    exit 1
else
    echo "将启动服务: ${service_name}"
fi

#localIP=`ifconfig | grep -Eo 'inet [0-9\.]+' | grep -v 127.0.0.1 | grep -Eo '[0-9\.]+' | head -2 | tail -1` # 类似实体机如mac有多个网口（wifi和usb网线）取最后一个
localIP="0.0.0.0"
if [[ ${service_name} = "seq" ]]; then
    echo "执行 seq， 依次启动各个服务: "
    allServiceStr="age,gender,nsfw_obj,nsfw,nsfw_bcnn,nsfw_ensemble,nonage,obj,ethnicity,cutcut_profile"
    allService=(${allServiceStr//,/ })
    echo "allService as :"
    for service in ${allService[@]};do echo $service;done
    read -r -p "confirm services [y/n] " input

    if [[ ${input} = "n" ]]; then
        echo "exit..."
        exit 1
    elif [[ ${input} = "y" ]]; then
        for service in ${allService[@]};
        do
            echo "    开启 ${service}"
            python -u _start_service_separate.py --service ${service} --host ${localIP}
        done
    fi
elif [[ ${service_name} = "all" ]]; then
    echo "*** all方式废弃 ***"
    echo "实现上为了兼容会非常冗杂，需要手动更改配置文件或者传入指定的配置文件"
    echo "并且性能上还会有下降，一个server多个接口也不能并发执行"
    echo "例如子服务的server上有四个子服务，gunicorn只给了2个worker，那么profile的server每次基本只有两个请求能成功"
    exit 0
#    echo "执行 all| step1: 先在一个server上启动所有子服务: "
#    python -u _start_service_separate.py --service ${service_name} --host ${localIP}
#    echo "执行 all| step2: 单独开启一个profile服务: "
#    python -u _start_service_separate.py --service cutcut_profile --host ${localIP}
else
    python -u _start_service_separate.py --service ${service_name} --host ${localIP}
fi

