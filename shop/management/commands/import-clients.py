# -*- coding: utf-8 -*-
import re
import json
from django.conf import settings
from pprint import pprint
from locked_pidfile.django_management import single
from django.core.management.base import BaseCommand

import requests
from django.utils.http import urlencode
from shop.utils import BASE_URL, SHOP_ID
from shop.utils import _normalize_phone, paginate_retailcrm
from shop.utils import process_api_error

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):
        # Use ods2json script from node.js to confert Excel to JSON
        data = json.loads(open('./data/frontpad-clients.json').read())
        # pprint(data)
        t = data['body']['tables'][0]

        EXISTING_CLIENT_NUMBERS = set()
        args = [
        ]
        for data in paginate_retailcrm('/customers', args):
            for c in data['customers']:
                for ph in c['phones']:
                    EXISTING_CLIENT_NUMBERS.add(_normalize_phone(ph['number']))
        pprint(EXISTING_CLIENT_NUMBERS)
        assert len(EXISTING_CLIENT_NUMBERS) > 100

        # Филиал | Имя | Телефон | Улица | Дом | Подъезд | Этаж | Квартира | Комментарий | Email | Не отправлять SMS | Дисконтная карта | Скидка | Лицевой счет | День рождения | Создан | Канал продаж |
        # x, name, phone, street, home, y, z, apt, comment, email, no_sms, card, discount, account, birthday, created, channel
        for num, row in enumerate(t['rows'][1:]):
            x, name, phone, street, home, y, z, apt, comment, email, no_sms, card, discount, account, birthday, created, channel = map(lambda c: c['value'], row['cells'])

            addr_list = [street]
            if home:
                addr_list.append(u'дом '+home)
            if apt:
                addr_list.append(u'кв. '+apt)
            address = u', '.join(addr_list)
            if u'перово' in address.lower() and u'утренняя' in address.lower() and '14' in address.lower():
                address = ''

            phones = map(lambda x: _normalize_phone(x.strip()), phone.split(','))
            # print name, '|', phones, '|', comment, '|', email, '|', created, '|', address

            found = False
            for p in phones:
                if p in EXISTING_CLIENT_NUMBERS:
                    print "-- ALREADY FOUND -- add manually"
                    print "      ", name, '|', phones, '|', comment, '|', email, '|', created, '|', address
                    found = True
            if found:
                continue

            created_iso = datetime.strptime(created, '%d.%m.%Y').date().isoformat()
            
            print "  adding ", name
            payload = {
                'firstName': name,
                'email': email,
                'commentary': comment,
                'phones': [{'number': p} for p in phones],
                'address': {'text': address},
                'createdAt': created_iso+' 00:00:00',
                'contragent': {'contragentType': 'individual'},
                'externalId': 'frontpad2016__{}'.format(num),
            }
            pprint(payload)
            url = "{}{}".format(BASE_URL, '/customers/create')
            r = requests.post(url, data={
                'apiKey': settings.RETAILCRM_API_SECRET,
                'site': SHOP_ID,
                'customer': json.dumps(payload),
            })
            process_api_error(r)


from datetime import datetime
from dateutil.parser import parse as parse_datetime
