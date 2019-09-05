#!/usr/bin/env bash
set -e
source ~/anaconda3/etc/profile.d/conda.sh
conda activate cv3.6

localIP=$1
if [[ ! -n "${localIP}" ]]; then
    localIP=`ifconfig | grep -Eo 'inet [0-9\.]+' | grep -v 127.0.0.1 | grep -Eo '[0-9\.]+' | head -1` # 类似实体机如mac有多个网口（wifi和usb网线）取第一个
    echo "未输入ip参数，自动获取ip: ${localIP}"
else
    echo "在ip: ${localIP} 启动服务"
fi

dt=`date +%Y-%m-%d_%H:%M:%S`
logDir="./CVServer/logs"
if [[ ! -d ${logDir} ]]; then
    echo "没有log目录，直接新建"
    mkdir ./CVServer/logs
fi

logfile="${logDir}/localhost_access_log.log"
if [[ -f ${logfile} ]]; then
    echo "上次的日志文件cp加上日期时间后缀（精确到秒）"
    \cp ${logfile} ${logfile}.${dt}
fi

nohup python -u manage_cutcut_server.py runserver ${localIP}:8000 > ${logfile}  2>&1 &

