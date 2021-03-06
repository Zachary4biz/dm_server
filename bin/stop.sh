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
    echo " vectorize       |8005|         关闭 [图片向量化] 服务"
    echo " ethnicity       |8006|         关闭 [人种分类] 服务"
    echo " nsfw_obj        |8007|         关闭 [鉴黄obj] 服务"
    echo " nsfw_bcnn       |8008|         关闭 [鉴黄bcnn] 服务"
    echo " nsfw_ensemble   |8009|         关闭 [鉴黄总承] 服务"
    echo " cutcut_profile  |8000|         关闭 [画像总成] 服务"
    exit 1
else
    if [[ ${service_name} = "all" ]]; then
        allServiceStr="age,gender,nsfw_obj,nsfw_bcnn,nsfw_ensemble,obj,ethnicity,cutcut_profile"
        allService=(${allServiceStr//,/ })
        echo "allService as :"
        for service in ${allService[@]};do echo $service;done
        read -r -p "confirm services [y/n] " input
        
        if [[ ${input} = "n" ]]; then
            echo "exit..."
            exit 1
        elif [[ ${input} = "y" ]]; then
            for service in ${allService[@]}
            do
                echo "将kill服务: ${service}"
                # python -u _stop_service.py ${service}
                ps -ef | grep gunicorn | grep ${service}  | awk '{print $2}' | xargs kill -9
            done
        fi
    else
        echo "将kill服务: ${service_name} details as:"
        ps -ef | grep gunicorn | grep ${service_name}
        ps -ef | grep gunicorn | grep ${service_name}  | awk '{print $2}' | xargs kill -9
#        python -u _stop_service.py ${service_name}
    fi
fi


echo "remaining service cnt as follow:"
ps -ef | grep "cutcut" | wc -l
