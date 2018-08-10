# -*- coding: utf-8 -*-
import re
import json

from locked_pidfile.django_management import single
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dateutil.parser import parse
from django.conf import settings
from shop.models import (
    Product,
)

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

from shop.utils import paginate_retailcrm

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):

        from shop.models import Order
        order = Order.objects.get(retailcrm_order_id=664)
        from pprint import pprint
        # pprint(order.data)

        from shop.api import _order_to_retail_crm
        print("-------------------------------------------------------")
        items = _order_to_retail_crm(order)
        for i in items:
            print(i['name'])
            pprint(i)
            print("------------------")
