# -*- coding: utf-8 -*-
from nose.tools import ok_, eq_
from shop.utils import _normalize_phone

def test():
    eq_(_normalize_phone('+79851115516'), '+79851115516')
    eq_(_normalize_phone('89851115516'), '+79851115516')
    eq_(_normalize_phone('9851115516'), '+79851115516')

    eq_(_normalize_phone('+7 985 111 55 16'), '+79851115516')
    eq_(_normalize_phone('8 985 111 55 16'), '+79851115516')
    eq_(_normalize_phone('985 111 55 16'), '+79851115516')

    eq_(_normalize_phone('+7 (985) 111-55-16'), '+79851115516')
    eq_(_normalize_phone('8 (985) 111-55-16'), '+79851115516')
    eq_(_normalize_phone('(985) 111-55-16'), '+79851115516')

    
    
    # bad numbers
    eq_(_normalize_phone('51115516'), '51115516')
    eq_(_normalize_phone('932139183'), '932139183')
