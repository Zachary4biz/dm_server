# encoding:utf-8
"""CVServer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
# from django.urls.resolvers import RegexURLPattern
from django.views.decorators.csrf import csrf_exempt
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), "../../")))
from CVServer import basic_view
from apps.age import age_service
from apps.gender import gender_service
from apps.nsfw import nsfw_service
from apps.obj_detection import yolo_service
from apps.cutcut import cutcut_profile

# django2 没有RegexURLPattern这个类了，暂时没解决，取消获取所有url的接口
# def api_index(request):
#     res = get_all_url(urlpatterns, prev='/')
#     return HttpResponse(json.dumps(res))


# def get_all_url(urlparrentens, prev, is_first=False):
#     result = []
#     for item in urlparrentens:
#         v = item._regex.strip('^$')  # 去掉url中的^和$
#         if isinstance(item, RegexURLPattern):
#             result.append(prev + v)
#         else:
#             get_all_url(item.urlconf_name, prev + v)
#     return result

all_service_api_dict = {"age": [url(r'age', age_service.predict)],
                        "gender": [url(r'gender', gender_service.predict)],
                        "nsfw": [url(r'nsfw', nsfw_service.predict)],
                        "obj": [url(r'obj', yolo_service.predict)],
                        "cutcut_profile": [url(r'cutcut_profile', csrf_exempt(cutcut_profile.profile_direct_api)),
                                           url(r'cutcut_default_profile', csrf_exempt(cutcut_profile.default_profile))]
                        }

urlpatterns = []
if os.environ['SERVICE_NAME'] == "all":
    urlpatterns.extend(url(r'hello_post', basic_view.hello_post))
    for i in all_service_api_dict.values():
        urlpatterns.extend(i)
else:
    urlpatterns.extend(all_service_api_dict[os.environ['SERVICE_NAME']])


# urlpatterns = [
#     url(r'^admin', admin.site.urls),
#     url(r'hello', basic_view.hello),
#     # url(r'^$', api_index),
#     # url(r'api_index', api_index),
#     url(r'hello_post', basic_view.hello_post),
#     url(r'age', age_service.predict),
#     url(r'gender', gender_service.predict),
#     url(r'nsfw', nsfw_service.predict),
#     url(r'obj_detection', yolo_service.predict),
#     url(r'cutcut_profile', csrf_exempt(cutcut_profile.profile_direct_api)),
#     url(r'cutcut_default_profile', csrf_exempt(cutcut_profile.default_profile)),
# ]
