# -*- coding: utf-8 -*-
import os
import emailer
DJANGO_ROOT = os.path.dirname(os.path.abspath(__file__)) + '/vk/'

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'vk',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

ALLOWED_HOSTS = ['new.vkusnyan.ru']
SITE_URL = "http://new.vkusnyan.ru"

USE_SENTRY = False

RAVEN_CONFIG = {
    'dsn': 'http://****:****@sentry7.highcat.org/***',
}

INTERNAL_IPS = ('127.0.0.1',
                '192.168.1.17',
                '172.16.227.168', # mac
                )

# SMTP_ACCOUNT = emailer.Account(
#     email='no-reply@iimagine.life',
#     fromname=u'I Imagine Life',
#     server='smtp.mandrillapp.com',
#     port='587',
#     ssl=True,
#     login='***',
#     password='***',
# )
