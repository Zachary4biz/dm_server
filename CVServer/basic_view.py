# encoding=utf-8
# 直接返回文字的Response
import os
import sys
import urls

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

