#!/usr/bin/env bash
pid_list=`ps -ef | grep "manage_cutcut_server.py runserver" | grep -v "grep" | awk '{print $2}'`
for res in ${pid_list}; do kill -9 ${res}; done
echo "remaining as follow:"
ps -ef | grep "cutcut"


