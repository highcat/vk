# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^$', 'shop.views.index'),
    url(r'^section/(?P<slug>[^/]+)/$', 'shop.views.section'),
    url(r'^discount/$', 'shop.views.discount'),
    url(r'^product/(?P<id>\d+)/(?:(?P<slug>[^/]+)/)?$', 'shop.views.product'),
    url(r'^a/(?P<id>\d+)/(?:(?P<slug>[^/]+)/)?$', 'shop.views.article'),
    url(r'^a/$', 'shop.views.article_list'),
    # 
    url(r'^sync/$', 'shop.views.sync'),
    # 
    url(r'^api/v1/order/complete/$', 'shop.api.order_complete'),
    url(r'^api/v1/order/update/$', 'shop.api.order_update'),
    url(r'^api/v1/op-days/$', 'shop.api.op_days'),
    url(r'^api/v1/op-days/(?P<day>\d{4}-\d{2}-\d{2})/status/(?P<day_status>open|closed)/$', 'shop.api.op_days_status'),
)
