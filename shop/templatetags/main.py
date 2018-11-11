# -*- coding: utf-8 -*-
import re
import pytz
import json
from django.conf import settings
from utils.utils import has_group
from jinja2 import Markup
from datetime import datetime
import anyjson
from shop.models import Section, Product
from django.contrib.auth.models import Group
from django_jinja import library
from jinja2 import contextfunction


@contextfunction
@library.global_function
def section_menu_link(context, slug):
    try:
        s = Section.objects.get(slug=slug)
    except Section.DoesNotExist:
        return Markup(u'<li {selected}><a href="/section/???/">раздел не существует</a></li>')

    selected = False
    if context.get('menu') == 'section-{}'.format(s.id):
        selected = True

    return Markup(u'<li {selected}><a href="/section/{slug}"/>{name}</a></li>'.format(
        selected=u'class="selected"' if selected == True else '',
        slug=s.slug,
        name=s.name,
    ))


@library.filter('has_group')
def _has_group(user, group_name):
    group = Group.objects.get(name=group_name) 
    return group in user.groups.all() 


@library.filter('jsonify_2_script')
def jsonify_2_script(data):
    return Markup(
        json.dumps(data, indent=4, ensure_ascii=False)
        .replace('<script>', '<scri"+"pt>')
        .replace('</script>', '</scri"+"pt>')
    );
