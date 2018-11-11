# -*- coding: utf-8 -*-
import re
import json

from locked_pidfile.django_management import single
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dateutil.parser import parse
from django.conf import settings
from shop.models import (
    Order
)
from shop.tasks import sync_order, book_order
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)


from vk.logs import log

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):
        qs = (
            Order.objects
            # Enable this line after ensure Celery is working:
#            .filter(created_at__lte=timezone.now()-timedelta(minutes=5 if settings.PROFILE != 'DEV' else 0))
            .filter(id__gte=280) # old orders on PROD
            .filter(
                Q(booked=False) |                
                Q(email_to_managers=False) |
                Q(sent_to_telegram_bot=False) |                
                # Q(email_to_customer=False) |
                Q(sent_to_retailcrm=False)
            )
        )
        print qs.count()
        for o in qs.values('id'):
            print 'Processing order', o['id']

            try:
                book_order(o['id'])
            except Exception:
                log.exception('book_order error')
                
            try:
                sync_order(o['id'])
            except Exception:
                log.exception('sync_order error')
