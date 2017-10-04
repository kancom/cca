from django.conf.urls import url
from .views import *

app_name = 'catalog'
urlpatterns = [
    url(r'^(?P<brand>[^/]+)?/?(?P<model>[^/]+)?/?(?P<gen>[^/]+)?/?(?P<modif>[^/]+)?/?$', ListCatalog.as_view(), name='listcatalog'),
    #~ url(r'^(?P<brand>[^/]+)/$', ListCatalog.as_view(), name='listcatalog'),
]
