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

from shop.utils import paginate_retailcrm, BASE_URL_V5

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):

        from shop.models import Order
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

        from shop.models import ProductOfferCount, Store, ProductOffer
        from vk.logs import log
        store_dict = dict((s.retailcrm_slug, s) for s in Store.objects.all())
        for data in paginate_retailcrm('/store/inventories', {
            'filter[details]': '1',
            'filter[offerActive]': '1',                
            'limit': '250',
        }, base_url=BASE_URL_V5):
            # pprint(data)
            for offer in data['offers']:
                # pprint(offer)
                # offer['id'], offer['quantity']
                for store in offer['stores']:
                    try:
                        store_dict[store['store']]
                    except KeyError:
                        log.exception('Need to add store to website')
                        pprint(offer)
                        print ProductOffer.objects.get(offer_id=offer['id']).product.short_name
                        continue
                    try:
                        oc = ProductOfferCount.objects.get(
                            offer__offer_id=offer['id'],
                            store=store_dict[store['store']],
                        )
                    except ProductOfferCount.DoesNotExist:
                        oc = ProductOfferCount(
                            offer=ProductOffer.objects.get(offer_id=offer['id']),
                            store=store_dict[store['store']],
                        )
                    oc.count = store['quantity']
                    oc.save()
