"""vk URL Configuration

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
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from ajax_select import urls as ajax_select_urls
import shop.urls

urlpatterns = [
    url(r'^', include(shop.urls)),
    url(r'^ajax_select/', include(ajax_select_urls)),
    url(r'^admin/', admin.site.urls),
]

# Serving static data for debug
if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'django.views.static.serve',
         {'document_root': settings.STATIC_ROOT, 'show_indexes': True}),
        (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
