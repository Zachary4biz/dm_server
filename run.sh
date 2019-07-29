#!/usr/bin/env bash

conda activate cv2.7
dt=`date +%Y-%m-%d_%H:%M:%S`
\cp ./CVServer/logs/localhost_access_log.log ./CVServer/logs/localhost_access_log.log.${dt}
nohup python -u manage_cutcut_server.py runserver 10.65.32.218:8000 > ./CVServer/logs/localhost_access_log.log &

