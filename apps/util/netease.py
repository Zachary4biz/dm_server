import hashlib
import time
import random
import urllib.request as urlrequest
import urllib.parse as urlparse
import json
from tqdm.auto import tqdm
import pickle
import os
PWD=os.path.dirname(__file__)

# level: 0：正常，1：不确定，2：确定
# label: 100色情 110性感
class NeteaseReq(object):
    """图片在线检测接口示例代码"""

    API_URL = "https://as.dun.163yun.com/v4/image/check"
    VERSION = "v4"

    def __init__(self):
        """
        Args:
            secret_id (str) 产品密钥ID，产品标识
            secret_key (str) 产品私有密钥，服务端生成签名信息使用
            business_id (str) 业务ID，易盾根据产品业务特点分配
        """
        self.secret_id = "b04a5ae51836b07e470155da0d3be4b9"  # 产品密钥ID，产品标识
        self.secret_key = "4ce6abbfa7b6c1c2ddb3a7b520b5f9fb"  # 产品私有密钥，服务端生成签名信息使用，请严格保管，避免泄露
        self.business_id = "efe70957241729256b46902d35388ce2"  # 业务ID，易盾根据产品业务特点分配

    def gen_signature(self, params=None):
        """生成签名信息
        Args:
            params (object) 请求参数
        Returns:
            参数签名md5值
        """
        buff = ""
        for k in sorted(params.keys()):
            buff += str(k) + str(params[k])
        buff += self.secret_key
        return hashlib.md5(buff.encode("utf8")).hexdigest()

    def check(self, params):
        """请求易盾接口
        Args:
            params (object) 请求参数
        Returns:
            请求结果，json格式
        """
        params["secretId"] = self.secret_id
        params["businessId"] = self.business_id
        params["version"] = self.VERSION
        params["timestamp"] = int(time.time() * 1000)
        params["nonce"] = int(random.random() * 100000000)
        params["signature"] = self.gen_signature(params)

        try:
            params = urlparse.urlencode(params).encode("utf8")
            request = urlrequest.Request(self.API_URL, params)
            content = urlrequest.urlopen(request, timeout=10).read()
            return json.loads(content)
        except Exception as ex:
            print("调用API接口失败:", str(ex))

    def request_porn(self,pic_url):
        images = [{"name":pic_url, "type":1, "data":pic_url}]
        params = {"images": json.dumps(images)}
        res_dict = self.check(params)
        if res_dict['code'] == 200:
            # res_dict示例:  {'code': 200, 'msg': 'ok', 'antispam': [{'taskId': '85500f51b20a4d0487d631d4639d432d', 'status': 0, 'action': 0, 'censorType': 0, 'name': 'https://thumbor.apusapps.com/imageView2/material/7ad3fc32/202002/112053/2f605524e3c14d6bb127330f278c8418.jpg', 'labels': [{'label': 100, 'level': 0, 'rate': 0.9988005, 'subLabels': []}, {'label': 110, 'level': 0, 'rate': 0.9985179, 'subLabels': []}, {'label': 900, 'level': 0, 'rate': 1.0, 'subLabels': []}]}], 'ocr': [{'taskId': '85500f51b20a4d0487d631d4639d432d', 'name': 'https://thumbor.apusapps.com/imageView2/material/7ad3fc32/202002/112053/2f605524e3c14d6bb127330f278c8418.jpg', 'details': []}], 'face': [{'taskId': '85500f51b20a4d0487d631d4639d432d', 'name': 'https://thumbor.apusapps.com/imageView2/material/7ad3fc32/202002/112053/2f605524e3c14d6bb127330f278c8418.jpg', 'details': []}], 'quality': [{'taskId': '85500f51b20a4d0487d631d4639d432d', 'name': 'https://thumbor.apusapps.com/imageView2/material/7ad3fc32/202002/112053/2f605524e3c14d6bb127330f278c8418.jpg', 'details': []}]}
            res = res_dict['antispam'][0]['labels']
            porn_res = [i for i in res if i['label']==100]
            try:
                pornRes=porn_res[0] if len(porn_res)>0 else {'level':0,'rate':1.0}
                label=pornRes['level']
                # level: 0：正常(图片)，1：不确定(的色情图片)，2：确定(的色情图片)
                rate=pornRes['rate']
                state = "success"
            except:
                label  = -1
                rate = 0.0
                # porn_res里应该是有label为100的，这个是色情检测的服务编号，没有它是异常情况
                state = str(porn_res)
        else:
            label=-1
            rate=0.0
            state="status_code as {}".format(res_dict['code'])
        return label,rate,state



if __name__ == "__main__":
    """示例代码入口"""
    api = NeteaseReq()
    # pornpics_kid: 
    img_url = "https://thumbor.apusapps.com/imageView2/material/7ad3fc32/202001/070306/5fd42f9e4d55461790af4c0ddf917d30.jpg"
    img_url = "https://static.picku.cloud/imageView2/material/7ad3fc32/202005/061750/9f2054af0e26486fbc64f82a1a94567b.jpg"
    print(">>> request_porn:")
    print(api.request_porn(img_url))
    print(">>> check:")
    images = [{"name":img_url, "type":1, "data":img_url}]
    params = {"images": json.dumps(images)}
    print(api.check(params))

    exit(0)
    # @deprecated
    # fp="/Users/zac/Downloads/porn_pics_kids.txt"
    fp="/Users/zac/Downloads/porn_urls_distinct.txt"
    with open(fp,"r+") as fr:
        porn_img_list=[i.strip() for i in fr.readlines() if len(i.strip())>0]
        porn_img_list=[i.split("?mode=")[0] for i in porn_img_list]

    print(porn_img_list[:5])
    porn_result=[]
    fail_urls_result=[]
    for idx,imgurl in tqdm(enumerate(porn_img_list[::])):
        images = [{"name":imgurl, "type":1, "data":imgurl}]
        params = {"images": json.dumps(images)}
        res_dict = api.check(params)
        try:
            res = res_dict['antispam'][0]
            porn_result.append(res)
        except Exception as e:
            fail_urls_result.append(imgurl)
        # if idx % 9==0 and idx>0:
            # time.sleep(1)
        time.sleep(0.5)

    with open(PWD+"/netease_porn_result.json","w+") as fw:
        for l in porn_result:
            fw.write(json.dumps(l)+"\n")
    
    with open(PWD+"/netease_porn_result.json","w") as fw:
        for url in fail_urls_result:
            fw.write(url+"\n")

    exit(0)

