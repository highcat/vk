# -*- coding: utf-8 -*-
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.cache import caches
from .models import SitePreferences
from vk.logs import log


class OrderProcessingError(Exception):
    pass

def process_api_error(response, silent=False, context_message=u"*some event*"):
    r = response
    if not (r.status_code >= 200 and r.status_code < 300):
        if r.status_code == 400:
            log.error(
                u"Error 400 on {}".format(context_message),
                extra={'response': r.json()},
            )
        else:
            log.error(
                u"Error {} on {}".format(r.status_code, context_message),
                extra={'response_text': r.text},
            )
        if not silent:
            raise OrderProcessingError()
        else:
            return False
    return True
    
    

def GET_SITE_PREFS():
    cache = caches['default']
    if cache.get('site_prefs'):
        return cache.get('site_prefs')
    try:
        obj = SitePreferences.objects.get(site__id=settings.SITE_ID)
    except SitePreferences.DoesNotExist:
        obj = SitePreferences(site=Site.objects.get()) # create 1st time
        obj.save()
    cache.set('site_prefs', obj, 120)
    return obj


import re
def _normalize_phone(phone):
    p = phone
    p = re.sub(r'[\s\(\)\-]+', '', p).strip()
    if p.startswith('+7'):
        return p
    if len(p) == len('9851115516'):
        return '+7' + p
    if len(p) == len('89851115516'):
        return '+7' + p[1:]
    return p




import requests
from django.utils.http import urlencode
BASE_URL = 'https://{}.retailcrm.ru/api/v4'.format(settings.RETAILCRM_ACCOUNT_NAME)
BASE_URL_V5 = 'https://{}.retailcrm.ru/api/v5'.format(settings.RETAILCRM_ACCOUNT_NAME)
SHOP_ID = settings.RETAILCRM_SHOP_ID
ALL_STORES = settings.RETAILCRM_ALL_STORES

def paginate_retailcrm(endpoint, args=None, base_url=BASE_URL):
    if not args:
        args = []
    if isinstance(args, dict):
        args = [(k, v) for k, v in args.iteritems()]
    has_more = True
    page = 1
    while has_more:
        a = []
        a += args
        a += [
            ('page', str(page)),
            ('apiKey', settings.RETAILCRM_API_SECRET),
        ]
        url = "{}{}?{}".format(base_url, endpoint, urlencode(a))
        r = requests.get(url)
        d = r.json()
        assert d['success'], d
        d['pagination']
        yield d
        has_more = d.get('pagination') and d['pagination']['currentPage'] < d['pagination']['totalPageCount']
        page += 1
