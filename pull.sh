#!/usr/bin/env bash


rsync -rvP  --rsh=ssh work@10.65.32.218:/data/work/cutcut-check/server/* ./

