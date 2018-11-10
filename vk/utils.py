from django.conf import settings
from django.core.cache import caches
from django.contrib.sites.models import Site


def GET_SITE_PREFS():
    cache = caches['default']
    if cache.get('site_prefs'):
        return cache.get('site_prefs')

    from vk.models import SitePreferences    
    try:
        obj = SitePreferences.objects.get(site__id=settings.SITE_ID)
    except SitePreferences.DoesNotExist:
        obj = SitePreferences(site=Site.objects.get()) # create 1st time
        obj.save()
    cache.set('site_prefs', obj, 120)
    return obj
