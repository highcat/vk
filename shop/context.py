# -*- coding: utf-8 -*-
"""Global template context"""
from vk.utils import GET_SITE_PREFS
from django.conf import settings
from .serializers import StoreSerializes
from .models import Store

def site_wide(request):
    return {
        'SITE_PREFS': GET_SITE_PREFS(),
        'settings': settings,
        'STORES': StoreSerializes(Store.objects.all(), many=True).data,
    }
