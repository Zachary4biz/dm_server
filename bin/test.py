# author: zac
# create-time: 2019-12-26 15:46
# usage: -

# 使用apache的ab工具对服务进行压测
import os
import sys
import json
from urllib.parse import quote
import subprocess
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), "../../")))
from config import CONFIG_NEW

img_url = quote("https://static.xprodev.com/imageView2/material/872d563e/201908/271519/2267895358_1566890382533.jpg?mode=0%26w=300%26h=300")
# 不想多加一个json文件，每次如果测profile就临时写一个吧
profile_request_json = json.dumps({'img_url': img_url, 'id': 'r', 'title': 'FM明星大片',
                                   'description': 'Rihanna以唐朝风发髻和妆容登上中国版BAZAAR 8月上封面，日日不愧是“山东人，扮起唐装一点也不违和😁'})

if __name__ == '__main__':
    tmp_fn = "tmp.json"
    with open(tmp_fn, "w") as f:
        f.writelines(profile_request_json)
    print(sys.argv)
    service_name = sys.argv[1]
    if service_name == "all":
        for service_name, serv_param in CONFIG_NEW.items():
            print(f"\n\n>>>> check service {service_name}")
            if service_name == "cutcut_profile":
                request_url = f"http://0.0.0.0:{serv_param.port}/{service_name}"
                status, output = subprocess.getstatusoutput(f"ab -n 50 -c 4 -T 'Content-Type:application/json' -p {tmp_fn} {request_url}")
                print(output)
            else:
                request_url = f"http://0.0.0.0:{serv_param.port}/{service_name}?img_url={img_url}&id=r"
                status, output = subprocess.getstatusoutput(r"ab -n 50 -c 4 '{}'".format(request_url))
                print(output)

        serv_param = CONFIG_NEW[service_name]

    else:
        print(f"\n\n>>>> check service {service_name}")
        serv_param = CONFIG_NEW[service_name]
        if service_name == "cutcut_profile":
            request_url = f"http://0.0.0.0:{serv_param.port}/{service_name}"
            status, output = subprocess.getstatusoutput(f"ab -n 50 -c 4 -T 'Content-Type:application/json' -p {tmp_fn} {request_url}")
        else:
            request_url = f"http://0.0.0.0:{serv_param.port}/{service_name}?img_url={img_url}&id=r"
            status, output = subprocess.getstatusoutput(r"ab -n 50 -c 4 '{}'".format(request_url))
        print(output)

    os.remove(tmp_fn)
