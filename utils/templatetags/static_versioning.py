# This module:
# a 'vstatic' tag, to generate URLs,
# also with modification timestamps for 'css' and 'js' files
#
# (c) Ivan Sagalaev
# (c) updated by HighCat
#
import re
import os
from django_jinja import library
from django.conf import settings

@library.filter('version_url')
def image_url(item):
    """versions for static files"""
    if isinstance(item, (str, unicode)):
        url = item
        fullname = os.path.join(settings.STATIC_ROOT, url).encode('utf-8')
        if os.path.exists(fullname):
            url += '?v=%d' % os.path.getmtime(fullname)
        return settings.STATIC_URL + url
    else:
        filefield = item
        if not filefield:
            return ''
        url = filefield.url
        fullname = os.path.join(settings.MEDIA_ROOT, filefield.name).encode('utf-8')
        if os.path.exists(fullname):
            url += '?v=%d' % os.path.getmtime(fullname)
        return url


@library.filter('i_resize')
def image_resize(url, width, height=None):
    """Transform to URL with image_filter by Nginx"""
    new_url = re.sub(ur'^/media/(.*)', '/media/resize/{}{}/\g<1>'.format(width, 'x{}'.format(height) if height else ''), url)
    if settings.PROFILE in ['PROD', 'STAGE']:
        return new_url
    return url

@library.filter('i_crop')
def image_crop(url, width, height=None):
    """Transform to URL with image_filter by Nginx"""
    new_url = re.sub(ur'^/media/(.*)', '/media/crop/{}{}/\g<1>'.format(width, 'x{}'.format(height) if height else ''), url)
    if settings.PROFILE in ['PROD', 'STAGE']:
        return new_url
    return url
        
