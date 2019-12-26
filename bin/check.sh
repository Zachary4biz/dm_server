#!/usr/bin/env bash
service_name=$1

if [[ ${service_name} = "all" ]]; then
    echo "执行 all， 依次检查各个服务: "
    for service in "age" "gender" "nsfw" "obj" "ethnicity" "vectorize" "cutcut_profile"
    do
        echo -e "\n\n>>>>> 检查 service: ${service}"
        ps -ef | grep gunicorn | grep ${service}
    done
else
    ps -ef | grep gunicorn | grep ${service_name}
fi

