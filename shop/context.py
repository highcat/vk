# -*- coding: utf-8 -*-
"""Global template context"""
from shop.utils import GET_SITE_PREFS
from django.conf import settings

def site_wide(request):
    return {
        'SITE_PREFS': GET_SITE_PREFS(),
        'settings': settings,
    }
