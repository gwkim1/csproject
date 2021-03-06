"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.contrib import admin



urlpatterns = [
    url(r'^results/', 'search.views.results', name="results"),
    url(r'^admin/', admin.site.urls),
    url(r'^home/', 'search.views.homepage', name="home"),
    url(r'^about/', 'search.views.about', name="about"),
    url(r'^detailed_results/', 'search.views.detailed_results', name="detailed_results"),
    url(r'^error/', 'search.views.error', name="error")
   ]



