# author: zac
# create-time: 2019-09-12 17:37
# usage: -

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), "../../")))
from zac_pyutils import ExqUtils
from zac_pyutils.ExqUtils import zprint
##################################################################
# **IMPORTANT*** 环境变量配置优先级最高，必须放在CONFIG_NEW模块引入之前
# --service 指定开启哪个服务 --host 指定ip
##################################################################
args_dict = ExqUtils.parse_argv(sys.argv)
SERVICE = args_dict['service']
HOST = args_dict['host']
os.environ.setdefault("SERVICE_NAME", str(SERVICE))  # urls.py config.py 里用到此环境变量
os.environ.setdefault("SERVICE_HOST", str(HOST))  # cutcut_profile.py 用到此环境变量（用于请求子服务）

import time
import requests
import subprocess
import datetime
from config import CONFIG_NEW, CONFIG_TFSERVING


def test_service(serv_name):
    PORT = CONFIG_NEW[serv_name].port
    post_params = {
        'img_url': 'http://scd.cn.rfi.fr/sites/chinese.filesrfi/dynimagecache/0/0/660/372/1024/578/sites/images.rfi.fr/files/aef_image/_98711473_042934387-1.jpg',
        'id': -1,
        'title': 'FM明星大片',
        'description': 'Rihanna以唐朝风发髻和妆容登上中国版BAZAAR 8月上封面，日日不愧是“山东人，扮起唐装一点也不违和😁'
    }
    url = f"http://{HOST}:{PORT}/{serv_name}"
    if serv_name == "all":
        # 如果是all不用发起任何请求
        b = time.time()
        res = ""
    elif serv_name != "cutcut_profile":
        url = url+"?img_url={}&id={}".format(post_params['img_url'], post_params['id'])
        zprint(">>> 测试get服务, 将请求url: {}".format(url))
        b = time.time()
        res = requests.get(url=url, timeout=60).text  # 第一次请求会初始化模型，超时时间设长一些
    else:
        zprint(">>> 测试post服务(profile), 请求url: {}".format(url))
        b = time.time()
        res = requests.post(url=url, data=post_params, timeout=60).text 
    zprint(">>> Test on {}: [time]:{:.3f}ms [res]:{}".format(serv_name, (time.time() - b)*1000, res))
    zprint("**上述计时包含了模型初始化时间**")


def start_server(serv_name):
    service_param = CONFIG_NEW[serv_name]
    PORT = service_param.port
    LOGFILE = service_param.host_logfile
    now = datetime.datetime.strftime(datetime.datetime.today(), "%Y-%m-%d_%H:%M:%S")

    if os.path.exists(os.path.dirname(LOGFILE)):
        if os.path.exists(LOGFILE):
            status, output = subprocess.getstatusoutput(r"\cp {} {}".format(LOGFILE, LOGFILE + "." + now))
            zprint("上次的日志文件cp加上日期时间后缀（精确到秒）. opt-status: {}".format(status))
    else:
        zprint("日志目录不存在，新建: {}".format(os.path.dirname(LOGFILE)))
        os.mkdir(os.path.dirname(LOGFILE))

    # gunicorn 启动
    gunicorn_cmd = f"""
    nohup gunicorn CVServer.wsgi:application \
    -b {HOST}:{PORT} \
    -w {service_param.worker_num} \
    --access-logfile {service_param.gunicorn_logfile} \
    --error-logfile {service_param.gunicorn_logfile+".opt"} \
    --timeout 200 \
    --worker-class eventlet \
    --daemon \
    --chdir {os.path.join(os.path.dirname(__file__), "..")} \
    2>&1 &
    """.strip()
    status, output = subprocess.getstatusoutput(gunicorn_cmd)
    zprint(">>> 启动服务 {} 于 {}:{} ".format(serv_name, HOST, PORT))
    zprint(">>> {}: subprocess status is: ' {} ', output is: ' {} '".format("SUCCESS" if status == 0 else "FAIL", status, output))


def start_tf_serving(serv_name):
    serv_params = CONFIG_TFSERVING[serv_name]
    cmd = f"""
    docker run -d --rm -p {serv_params.docker_port}:8501 \
        --name {serv_params.name} \
        -v "{serv_params.pb_path}:/models/{serv_params.name}" \
        -e MODEL_NAME={serv_params.name} \
        -t tensorflow/serving > {serv_params.logfile}  &
    """.strip()
    status, output = subprocess.getstatusoutput(cmd)
    zprint(">>> 启动内部TFServing服务 {} 于端口 {} ".format(serv_name, serv_params.docker_port))
    zprint(">>> {}: subprocess status is: ' {} ', output is: ' {} '".format("SUCCESS" if status == 0 else "FAIL", status, output))


if SERVICE == "all":
    assert False, "此部分逻辑已废弃"
    zprint("在同一端口下不同路由启动所有「子服务」")
    # assert False, "使用starts.sh里循环bash启动所有 | 不支持一个py内部起多个django服务，会导致environ冲突（属于同一个py进程，共用environ）"
    start_server(SERVICE)
    time.sleep(10)
    for i in CONFIG_NEW.keys():
        if i not in ["all"]:
            # all本身没有这个接口也不请求
            test_service(i)
else:
    if SERVICE in CONFIG_TFSERVING:
        zprint(f">>> 此服务 {SERVICE} 是转发请求到TFServing，将启动对应的TFServing服务")
        start_tf_serving(SERVICE)
    start_server(SERVICE)
    time.sleep(10)
    test_service(SERVICE)

# nohup python -u manage_cutcut_server.py runserver ${localIP}:8000 > ${logfile}  2>&1 &
