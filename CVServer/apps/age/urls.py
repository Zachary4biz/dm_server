from django.conf.urls import url    
from . import age_service

  
urlpatterns = [  
    url(r'predict', age_service.predict),  
] 