#!/usr/bin/env python
import os
import sys
import requests

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CVServer.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)

    serv_name = os.environ['SERVICE_NAME']
    HOST = os.environ['SERVICE_HOST']
    PORT = os.environ['SERVICE_PORT']
    if serv_name in ['age', 'nsfw', 'gender', 'obj']:
        url = "http://scd.cn.rfi.fr/sites/chinese.filesrfi/dynimagecache/0/0/660/372/1024/578/sites/images.rfi.fr/files/aef_image/_98711473_042934387-1.jpg"
        id_ = "r"
        request_url = "http://{}:{}/{}?img_url={}&id={}".format(HOST, PORT, serv_name, url, id_)
        print("begin requests ... {}".format(request_url))
        res = requests.get(request_url, timeout=8).text
        print(res)
