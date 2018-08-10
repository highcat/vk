# -*- coding: utf-8 -*-
import string

def has_group(user, groupname, or_superuser=False):
    if not user.is_authenticated():
        return False
    if or_superuser and user.is_superuser:
        return True
    return groupname in user.groups.values_list('name', flat=True)


class BlankFormatter(string.Formatter):
    """ ??? """
    def __init__(self, default=''):
        self.default = default

    def get_value(self, key, args, kwds):
        if isinstance(key, (str, unicode)):
            return kwds.get(key, self.default)
        else:
            string.Formatter.get_value(key, args, kwds)

