# -*- coding: utf-8 -*-
"""Redis connection"""
from redis import StrictRedis
from django.conf import settings

_redis = None

def get_redis():
    global _redis
    if not _redis:
        _redis = StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
    return _redis
