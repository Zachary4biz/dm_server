import requests
import time
import random
import json
from Crypto import Random
from Crypto.Hash import SHA256
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.PublicKey import RSA
import base64
from tqdm.auto import tqdm

# confluence文档 https://nowiki.apuscn.com/pages/viewpage.action?pageId=16293076

class TaskId():
    porn="54bcfc6c329af61034f7c2fc"
    terr="5e1d70adeec2874f7318dc52"
    ad="56a8645b0c800bff40990cf1"
    vulgar="5ad37309616505867eeac264"
    politic="5b7be1f59b0c77a8c2afb351"

class TupuReq(object):
    def __init__(self):
        self.secretID="563883b50e4f58f951a06d8e"
        self.api_url = f'http://api-us.open.tuputech.com/v3/recognition/{self.secretID}'
        self.privatekey="""-----BEGIN RSA PRIVATE KEY-----
        MIICWwIBAAKBgQCrzaze0785P3Mpty9urItTKRBE/eVLvikzC/f4kJtT51PL3sSX
        S7Wrn7xoQJnRCkrYjB6wr19grFyNTgnTGT+/yYyL0aGzE8SaR0ZzbTkIgZbQd+/G
        QcY+ckRbQTIsWb0xt9vTsa/Lbd/ZRiYnMIxk2e5InZZSplguH1WMV6cZqwIDAQAB
        AoGAIZVsBIbp63vuvCnV+NF7zr7JMmNbTkoW7aaaS5mg827V35VlYpnnImxwPQTb
        zJQxe1EwsqMlhtVKpkip/P0Di9z/VCJLlBpRtlAiOlN8Bjvw1eND11Lj/aNcdYhY
        FC4z4CTIk4qQ/O8mjN6E9frKUO+mDGOozo6oKsmEaMN0ClECQQDam2gWHnrSbEkB
        nejxLdbUt0ZcSuhRVeScNOJagiFTV1/lz+3gsNZbSCC8UU2Jr5LyHyS6dS+xiXV1
        RnhZvEtDAkEAyTDIQjPcKAzo3WrI6qliO/gFmY+sYx0xGqjXtB5wDXNXUAYYoT8S
        fA1mOk2dzub6CB8mkh15sUVj9qERKDRteQJAHkcJ+o5MKprO3cd2PPlBWQLtXtkN
        Jj7ERBJbC3gcj4N5h8Xtx4IWnlv2FL8aAyjrLFe96YlTir5kI1MYVi1rKwJAKB00
        4JZMgCPKzlL7SmaJcqGKJEsUORLZ9pHRqFUlTFlCAG+mu4fC3L8jMd7F5zoAglwL
        qbh8yg6m1sbYj+acKQJACU2DTRBKehCpETBT8GYtoWQLz2UYuMfAu6+c2eMOoWLk
        ZL5xHIZJCGEN7n6acwMFHVCPNNXUn4Hiol1FKyuUKA==
        -----END RSA PRIVATE KEY-----"""
    
    def request(self,pic_url,tasks=None):
        # 默认情况会请求所有task
        if tasks is None:
            tasks=[TaskId.__getattribute__(TaskId,i) for i in dir(TaskId) if not i.startswith("__")]
        t = str(int(time.time()))
        nonce=str(random.random())
        signature = self.get_signature(t,nonce)
        params={'image':pic_url,'timestamp':t,'nonce':nonce,'signature':signature}
        _ = [params.update({"task":t}) for t in tasks]
        res=requests.post(url=self.api_url,data=params)
        return res

    # label为7是检测到未成年
    def request_vulgar(self,pic_url):
        res=self.request(pic_url,tasks=[TaskId.vulgar])
        if res.status_code == 200:
            jsonPart=json.loads(res.text)['json']
            try:
                vulgarRes=json.loads(jsonPart)[TaskId.vulgar]
                label=vulgarRes['fileList'][0]['label']
                rate=vulgarRes['fileList'][0]['rate']
                state = "success"
            except:
                label  = -1
                rate = 0.0
                state = json.loads(jsonPart)['message']
        else:
            label=-1
            rate=0.0
            state="status_code as {}".format(res.status_code)
        return label,rate,state
    
    # label: 0 色情 露点、生殖器官、性行为等
    # label: 1 性感 露肩、露大腿、露沟等
    # label: 2 正常
    # 重新映射为 0是正常(2,1->0)，1是色情(0->1)
    remap={0:1,1:0,2:0}
    def request_porn(self,pic_url):
        res=self.request(pic_url,tasks=[TaskId.porn])
        if res.status_code == 200:
            jsonPart=json.loads(res.text)['json']
            try:
                pornRes=json.loads(jsonPart)[TaskId.porn]
                label=pornRes['fileList'][0]['label']
                rate=pornRes['fileList'][0]['rate']
                state = "success"
            except:
                label  = -1
                rate = 0.0
                state = json.loads(jsonPart)['message']
        label = self.remap.get(label,label)
        return label,rate,state


    def get_signature(self,t,nonce):
        message=(self.secretID+","+t+","+nonce).encode("utf-8")
        signature=self.sign(message,self.privatekey)
        return signature

    @staticmethod
    def sign(message,privatekey):
        rsakey = RSA.importKey(privatekey)
        signer = Signature_pkcs1_v1_5.new(rsakey)
        digest = SHA256.new()
        digest.update(message)
        sign = signer.sign(digest)
        signature = base64.b64encode(sign)
        return signature

if __name__ == "__main__":
    tupuReq = TupuReq()
    pic_url="https://static.picku.cloud/imageView2/material/7ad3fc32/202002/261211/0cce922725f047f9b9ad0e2e19bf06a9.jpg"
    pic_url = "https://static.picku.cloud/imageView2/material/7ad3fc32/202005/062139/a00ab025d3ae4cbca078f813c7b2af9a.jpg"
    # porn_lbl,porn_rate=tupuReq.request_porn(pic_url)
    print(tupuReq.request_porn(pic_url))
    # child_lbl,child_rate=tupuReq.request_vulgar(pic_url)
    print(tupuReq.request_vulgar(pic_url))