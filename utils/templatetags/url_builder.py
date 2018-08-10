# -*- coding: utf-8 -*-
from copy import deepcopy
from django_jinja import library

@library.filter('p_set')
def p_set(d, **kw):
    d = deepcopy(d)
    d.update(kw)
    return d

@library.filter('p_inc')
def p_inc(d, **kw):
    d = deepcopy(d)
    for k, w in kw.iteritems():
        if not d.get(k):
            d[k] = 1 # FIXME
        d[k] = int(d[k])+int(w)
    return d

@library.filter('p_dec')
def p_dec(d, **kw):
    d = deepcopy(d)
    for k, w in kw.iteritems():
        if not d.get(k):
            d[k] = 1 # FIXME
        d[k] = int(d[k])-int(w)
    return d

@library.filter('p_append')
def p_append(d, **kw):
    d = deepcopy(d)
    for k, v in kw.iteritems():
        if k in d:
            if isinstance(d[k], unicode):
                d[k] = d[k].split(',')
            d[k].append(v)
        else:
            d[k] = [v]
    return d

@library.filter('p_del')
def p_del(d, *args, **kw):
    """
    Use it to delete something from list:

       p_del(tags='mytag')

    To delete everything, do the following:

       p_del('tags')

    """
    d = deepcopy(d)

    for k in args:
        if k not in d:
            continue
        del d[k]

    for k, v in kw.iteritems():
        if k not in d:
            continue
        if isinstance(d[k], unicode) and d[k] == v:
            del d[k]
        else:
            d[k] = d[k].split(',')
            d[k].remove(v)
            if not d[k]:
                del d[k]
    return d

@library.filter('p_url')
def p_url(d):
    # remove duplications in lists:
    for k in d.keys():
        if isinstance(d[k], list):
            d[k] = list(set(d[k]))
    return '&'.join([
        "%s=%s" % (k, ','.join(v) if isinstance(v, list) else v)
        for k, v in d.items()
    ])

@library.filter('p_in')
def p_in(item, where):
    if isinstance(where, unicode):
        where = where.split(',')
    return item in where
