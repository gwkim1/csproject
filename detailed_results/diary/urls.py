

from django.conf.urls import url
from django.contrib import admin

from django.http import HttpResponse

from . import views

urlpatterns = [
    url(r'^$', views.d_results, name='d_results'),
    #url(r'^about/$', views.about, name='about'),
    #url(r'^pie/$', views.pie, name='pie'),
]

