# encoding:utf-8
import requests
import time
xjp = ["xjp", "https://upload.wikimedia.org/wikipedia/commons/e/ed/Xi_Jinping_2016.jpg"]
emma = ["emma", "http://n.sinaimg.cn/front/241/w552h489/20190204/vYlJ-hsmkfyp5208900.jpg"]
nsfw1 = ["nsfw1",
         "https://img-blog.csdn.net/20170826160523111?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvc3BhcmtleHBlcnQ=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/Center"]
nsfw2 = ["nsfw2",
         "https://img-blog.csdn.net/20170826160402172?watermark/2/text/aHR0cDovL2Jsb2cuY3Nkbi5uZXQvc3BhcmtleHBlcnQ=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/Center"]
img_list = [xjp, emma, nsfw1, nsfw2]

print(">>>所有API接口:")
print(requests.get("http://10.65.32.218:8000/api_index").text)

for id_, url in img_list:
    print(">>>{}".format(id_))
    b = time.time()
    res = requests.get("http://10.65.32.218:8000/age?img_url={}&id={}".format(url, id_)).text
    e = time.time()
    print("  年龄 of {}: [res]:{} [time]:{}".format(id_, res, str(e-b)))
    b = time.time()
    res = requests.get("http://10.65.32.218:8000/gender?img_url={}&id={}".format(url, id_)).text
    e = time.time()
    print("  性别 of {}: [res]:{} [time]:{}".format(id_, res, str(e-b)))
    b = time.time()
    res = requests.get("http://10.65.32.218:8000/nsfw?img_url={}&id={}".format(url, id_)).text
    e = time.time()
    print("  鉴黄 of {}: [res]:{} [time]:{}".format(id_, res, str(e - b)))
