# encoding=utf-8

from django.http import HttpResponse

# 返回渲染过的html页面
from django.shortcuts import render
outside_value="abc"
def hello(request): 
	context = {} 
	context['param1'] = outside_value 
	context['section'] = request.GET['section'] if 'section' in request.GET else ''
	return render(request, 'basic_view.html', context)

def hello_post(request):
	sec = request.POST['section'] if 'section' in request.POST else ''
	return render(request, 'basic_view.html', {"param1":"First Param","section":sec})

import json
def test(request):
	params = request.GET
	if 'img_url' in params and 'id' in params:
		json_str = json.dumps({"img_url":params["img_url"], "id":params["id"]})
		return HttpResponse(json_str, status=200, content_type="application/json,charset=utf-8")
