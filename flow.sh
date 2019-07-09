#!/usr/bin/env bash
# 只会同步修改过的文件
rsync -rvP  --rsh=ssh ./* work@10.65.32.218:/data/work/cutcut-check/server/



