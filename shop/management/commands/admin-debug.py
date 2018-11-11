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
from pprint import pprint

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)
import requests

from shop.utils import paginate_retailcrm, BASE_API_URL

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):

        # from shop.models import Order
        # order = Order.objects.get(retailcrm_order_id=664)
        # from pprint import pprint
        # pprint(order.data)

        # from shop.api import _order_to_retail_crm
        # print("-------------------------------------------------------")
        # items = _order_to_retail_crm(order)
        # for i in items:
        #     print(i['name'])
        #     pprint(i)
        #     print("------------------")

        from shop.models import Store
        store_dict = dict((s.retailcrm_slug, s) for s in Store.objects.all())
        for data in paginate_retailcrm('/orders', {
            'limit': '20',
            'filter[ids][]': '1548',
        }):
            pprint(data)
            break

        
        item_id = 12506
        for data in paginate_retailcrm('/orders/packs', {
            'limit': '20',
            'filter[itemId]': item_id,
        }):
            pprint(data)
            break

        # Операция идемпотентна для одного склада.
        # 
        r = requests.post('https://smarta.retailcrm.ru/api/v5/orders/packs/create', data=
            {
                'apiKey': settings.RETAILCRM_API_SECRET,
                'pack': json.dumps({
                    'itemId': str(item_id),
                    'store': 'smarta-red-room',
                    # 'store': 'polus-tretyak',
                    # 'purchasePrice': None,
                    'quantity': 2,
                    # 'shipmentDate': None,
                    # 'invoiceNumber': None,
                    # 'deliveryNoteNumber': None,
                }),
            },
        )
        print r.status_code
        pprint(r.json())
