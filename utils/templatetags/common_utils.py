# -*- coding: utf-8 -*-
import pytz
from django.conf import settings
from utils.utils import has_group
from jinja2 import Markup
import anyjson
from django_jinja import library
from jinja2 import contextfunction


@library.filter('user_tz')
def user_tz(dt):
    return dt.astimezone(pytz.timezone(settings.TIME_ZONE))


@library.filter('has_group')
def has_group_(user, groupname, or_superuser=False):
    return has_group(user, groupname, or_superuser=or_superuser)


@library.filter
def jsonify_2_script(data):
    return Markup(
        anyjson.serialize(data)
        .replace('<script>', '<scri"+"pt>')
        .replace('</script>', '</scri"+"pt>')
    );


@library.filter
def shorten(text, max_len=70):
    if len(text) >= max_len:
        text = text[:max_len-1] + u'…'
    return text
