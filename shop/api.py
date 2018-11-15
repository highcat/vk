# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404

import re
import math
import json
import requests
from copy import deepcopy
from pprint import pprint
from rest_framework import mixins
from rest_framework import filters
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from datetime import timedelta, datetime, date
from django.utils import timezone
from django.db import transaction, connection
from django.db.models import F, Q
from django.conf import settings
from .utils import process_api_error

from .models import Product, Order, PromoCode, AutoPromoCode, OperationalDay, Store

from . import tasks
from .utils import _normalize_phone
from .utils import paginate_retailcrm
from shop.utils import SHOP_ID, BASE_API_URL

from django import forms
from django.forms import ValidationError


class OrderForm(forms.Form):
    promo_code = forms.CharField(max_length=100, required=False)
    contact_name = forms.CharField(max_length=100, required=False)
    contact_phone = forms.CharField(max_length=100)
    contact_email = forms.EmailField(required=False)
    contact_address = forms.CharField(max_length=500, required=False)
    delivery = forms.CharField(max_length=100)

    note = forms.CharField(required=False, max_length=500)

    def clean_promo_code(self):
        code = self.cleaned_data.get('promo_code')
        if not code:
            return ''
        return code

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        phone = re.sub(ur'[\-\(\)\s]+', '', phone).strip()
        if not re.match(ur'^[0-9\+]{5,20}$', phone):
            raise ValidationError(u'Введите корректный телефон')
        return phone

    def clean(self):
        delivery = self.cleaned_data.get('delivery')
        contact_address = self.cleaned_data.get('contact_address', '').strip()
        if delivery == 'delivery':
            if not contact_address:
                self.add_error('contact_address', u"Введите адрес!")
        elif delivery == 'delivery-post':
            if not contact_address:
                self.add_error('contact_address', u"Введите адрес!")
        elif delivery and delivery.startswith('selfdelivery--'):
            store = delivery[len('selfdelivery--'):]
            if not Store.objects.filter(retailcrm_slug=store).exists():
                self.add_error('delivery', u"Неизвестный склад!")
        else:
            self.add_error('delivery', u"Неизвестный способ доставки!")


@transaction.atomic
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def order_complete(request):
    data = request.data

    # 1. Perform OrderUpdate
    data = _order_update(data)
    warnings = data['warnings']
    new_warnings = data['new_warnings']
    errors = data['errors']
    
    # 2. validate OrderForm
    form = OrderForm(data=data)
    if not form.is_valid():
        for key, value in form.errors.items():
            errors[key] = value.as_text()
    #.. and update some fields
    data['contact_phone'] = _normalize_phone(data['contact_phone'])
    is_by_operator = request.user.is_authenticated() and request.user.groups.filter(name='operators').exists()
    if not is_by_operator:
        data['op_phone_order'] = False
        data['status_confirmed'] = False
            
    # 3. Return:
    # - if errors or new warnings: return the data with errors & warnings
    # - if everything's ok - place order

    # print 'errors', errors
    data['errors'] = errors
    data['warnings'] = warnings
    data['new_warnings'] = new_warnings
    if errors or new_warnings:
        return Response(data, status.HTTP_200_OK)

    # 2. Create order object
    order = Order(data=data)
    order.save()

    # 3. Update promo code
    if data.get('code'):
        code = data.get('code')
        PromoCode.objects_active.filter(code__iexact=code).update(used_times=F('used_times')+1)
        AutoPromoCode.objects_active.filter(code__iexact=code).update(used_times=F('used_times')+1)

    # 4. Create on RetailCRM
    _order_det = _order_to_retail_crm(order)

    # Run post-processing task
    tasks.sync_order.delay(order.id)
    tasks.book_order.delay(order.id)

    data['order_sent'] = True
    # needed for Universal Analytics / Yandex Metrika
    data['order_id'] = _order_det['order_id']
    data['ua_items'] = _order_det['ua_items']

    assert data['total_price']
    assert data['order_id']
    return Response(data, status.HTTP_200_OK) # XXX error response returns 200 too



@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def order_update(request):
    data = request.data
    # TODO validate data format
    data['items'] = data.get('items') or []; # quick hack
    data = _order_update(data)
    return Response(data, status.HTTP_200_OK) # XXX error response returns 200 too


def _order_update(data):
    u"""Update order:
    - Check products & prices are available & valid.
    - Return warnings if something changed.
    - Return discount.
    """
    # keep old warnings, append new
    warnings = {}
    errors = {}
    discounts = {
        'variable': 0, # percents
        'fixed': 0,
        'names': [], # сообщение от промо-кода
    }
    def _clear_initial_warning(key):
        data.get('warnings', {}).pop(key, None)

    if data.get('code'):
        pc = None
        msg = u'Такого кода нет'
        # Try to get actual code
        if not pc:
            try:
                pc = PromoCode.objects_active.get(code__iexact=data.get('code'))
            except PromoCode.DoesNotExist:
                pass
        if not pc:
            try:
                pc = AutoPromoCode.objects_active.get(code__iexact=data.get('code'))
            except AutoPromoCode.DoesNotExist:
                pass
        if pc:
            _clear_initial_warning('invalidPromoCode')
            discounts['variable'] = pc.variable_discount
            discounts['fixed'] = pc.fixed_discount
            discounts['names'].append(pc.name)
        else:
            # Try to find outdated code, to show message
            outdated_pc = None
            if not outdated_pc:
                outdated_pc = PromoCode.objects.filter(code__iexact=data.get('code')).order_by('-created_at').first()
            if not outdated_pc:
                pc = AutoPromoCode.objects.filter(code__iexact=data.get('code')).order_by('-created_at').first()
            if outdated_pc:
                active, msg = outdated_pc.is_active_and_msg() # get more specific message
            warnings['invalidPromoCode'] = msg
    else:
        _clear_initial_warning('invalidPromoCode')
                
    # Calculate total price
    items_to_delete = []
    _clear_initial_warning('itemMissing')
    _clear_initial_warning('pricesUpdated')
    for d in data['items']:
        try:
            product = (
                Product.objects
                .filter(Q(in_stock=True) | (
                    Q(preorder__isnull=False) | Q(is_market_test=True)
                ))
                .get(id=d['id'])
            )
            if product.is_product_kit:
                d['is_kit'] = True
        except Product.DoesNotExist:
            items_to_delete.append(d['id'])
        else:
            if not (product.preorder or product.is_market_test):
                # TODO разбить здесь наборы на составляющие, и проверять реальные остатки.
                if (d['count'] > product.count_available):
                    d['count'] = product.count_available
                    if d['count'] == 0:
                        items_to_delete.append(d['id'])
                    else:
                        warnings['noEnoughInStock'] = u'Некоторых товаров не хватает на складе. Корзина обновлена.'
            if (d['price'] != product.price or
                (d.get('discount_price') or None) != (product.discount_price or None)):
                d['price'] = product.price
                d['discount_price'] = product.discount_price
                warnings['pricesUpdated'] = u'Цены на некоторые товары обновились.'
            if product.preorder and not product.in_stock:
                d['preorder'] = datetime.strftime(product.preorder, '%d.%m.%Y')

    if len(items_to_delete):
        warnings['itemMissing'] = u'Некоторые товары закончились на складе и удалёны из корзины.'
    data['items'] = filter(lambda i: i['id'] not in items_to_delete, data['items'])
        
    # Warnings w/o actions:
    # warnings['notePromoCode'] = u'Осталось только 2 срабатывания этого кода. Спешите сделать заказ!'
    # warnings['noteItem'] = u'Товар <имя> заканчивается! Спешите!'

    data['items_price'] = 0
    for i in data['items']:
        data['items_price'] += (i.get('discount_price') or i['price']) * i['count']
    data['total_price'] = data['items_price']
    data['total_price'] *= (1-discounts['variable']/100.)
    data['total_price'] -= discounts['fixed']
    if data['total_price'] < 0:
        data['total_price'] = 0
    data['total_price'] = math.floor(data['total_price'])

    data['discounts'] = discounts
    data['new_warnings'] = bool(set(warnings.keys()) - set(data.get('warnings', {}).keys()))
    data['warnings'] = data.get('warnings', {})
    data['warnings'].update(warnings)
    data['errors'] = errors
    return data



def _order_to_retail_crm(order):
    u"""Syncs order to RetailCRM.
    No transactions inside.
    
    Assuming data is already checked for correctness.
    Just throw error, if it's not correct.
    """
    # Expand kits,
    # populate with retailcrm_id
    # also collect all offers
    items = []
    all_offers = set()
    for d in order.data['items']:
        p = Product.objects.prefetch_related('retailcrm_offers', 'kit_items').get(id=d['id'])
        # Add the product, or kit itself
        d['retailcrm_id'] = p.retailcrm_id
        d['offer_ids'] = list(p.retailcrm_offers.values_list('offer_id', flat=True))
        d['from_kit'] = False
        d['is_kit'] = p.is_product_kit
        items.append(d)
        all_offers |= set(p.retailcrm_offers.values_list('offer_id', flat=True))
        # Add kit items
        if p.is_product_kit:
            for kit_item in p.kit_items.prefetch_related('product', 'product__retailcrm_offers').order_by('order'):
                items.append({
                    'id': kit_item.product.id,
                    'name': kit_item.product.short_name,
                    'retailcrm_id': kit_item.product.retailcrm_id,
                    'offer_ids': list(kit_item.product.retailcrm_offers.values_list('offer_id', flat=True)),
                    'count': kit_item.count * d['count'],
                    'price': 0,
                    'discount_price': 0,
                    'sum': 0,
                    'from_kit': True,
                    'is_kit': False
                })
                all_offers |= set(kit_item.product.retailcrm_offers.values_list('offer_id', flat=True))

    #### Merge item duplications (they may exist because of kits)
    # Find groups
    groups = {}
    for idx, i in enumerate(items):
        if i['id'] not in groups:
            groups[i['id']] = {'items': [i], 'index': idx}
        else:
            groups[i['id']]['items'].append(i)
    # Merge groups with multiple items
    for id, g in groups.iteritems():
        if len(g['items']) > 1:
            total_sum = 0
            total_count = 0
            for i in g['items']:
                total_sum += (i['discount_price'] or i['price']) * i['count']
                total_count += i['count']
            i_1st = g['items'][0]
            g['items'] = [{
                'id': i_1st['id'],
                'name': i_1st['name'],
                'retailcrm_id': i_1st['retailcrm_id'],
                'offer_ids': i_1st['offer_ids'],
                'count': total_count,
                'sum': total_sum,
                'from_kit': True, # one of items from kit => assume from kit
                'is_kit': False
                # Not used:
                # 'price': 0,
                # 'discount_price': 0,
            }]
    # Groups back to list
    items = map(lambda x: x[0]['items'][0], sorted([(g, g['index']) for id, g in groups.iteritems()], key=lambda x: x[1]))

    # Fetch offers counts
    offer_counts = {}
    args = [
        ('filter[offerActive]', "1"),
    ]
    for o_id in all_offers:
        args.append(('filter[ids][]', o_id))
    for data in paginate_retailcrm('/store/inventories', args):
        for o in data['offers']:
            offer_counts[o['id']] = o['quantity']

    # Decide which offers to use; split if necessary
    splitted_items = [] # (id, item)
    for i in items:
        if i['is_kit']:
            i['selected_offer_id'] = i['offer_ids'][0]
            # don't check count for kits
            continue
        offers = sorted([(oid, offer_counts[oid]) for oid in i['offer_ids']], key=lambda pair: pair[1])
        count_left = i['count']
        # start with lesser
        for oid, o_count in offers:
            if o_count == 0:
                continue
            if count_left <= o_count:
                i['count'] = count_left
                i['selected_offer_id'] = oid
                count_left = 0
                break
            else:
                new_item = deepcopy(i)
                new_item['count'] = o_count
                new_item['selected_offer_id'] = oid
                splitted_items.append((i['id'], new_item))
                count_left -= o_count
        if count_left > 0:
            p = Product.objects.get(id=i['id'])
            if p.preorder or p.is_market_test:
                i['selected_offer_id'] = offers[0][0] # first available offer id
            else:
                assert False, u"Not enough available count, probably website is not synchronized with CRM"
    # insert splitted items
    for id, new_i in splitted_items:
        idx = max(loc for loc, val in enumerate(items) if val['id'] == id)
        items.insert(idx+1, new_i)

    # Finally - Send Order!
    order_payload = {
        'contragent': 'individual',
        'orderType': 'eshop-individual',
        'orderMethod': 'phone' if order.data['op_phone_order'] else 'shopping-cart',
        'status': 'client-confirmed' if order.data['status_confirmed'] else 'new',
        # 'paymentType', ''
        'firstName': order.data['contact_name'],
        'phone': order.data['contact_phone'],
        'email': order.data.get('contact_email'),
        'customerComment': order.data.get('note'),
        'discount': {},
        'delivery': {},
        'items': [],
        # # TODO привязка к кампании
        # 'source': {
        #     'source': '',
        #     'medium': '',
        #     'campaign': '',
        #     'keyword': '',
        #     'content': '',
        # },
    }

    if order.data['discounts']['fixed']:
        order_payload['discount'] = order.data['discounts']['fixed']
    if order.data['discounts']['variable']:
        order_payload['discountPercent'] = order.data['discounts']['variable']


    if order.data.get('delivery').startswith('selfdelivery--'):
        store = Store.objects.get(retailcrm_slug=order.data['delivery'][len('selfdelivery--'):])
        # shipmentStore - просто выставляет склад отгрузки. Не бронирует.
        order_payload['shipmentStore'] = store.retailcrm_slug
        order_payload['delivery']['code'] = 'self-delivery'
        order_payload['delivery']['address'] = {'text': store.address}
        # order_payload['delivery']['cost'] = ...
    else:
        order_payload['delivery']['code'] = 'some-delivery'
        order_payload['delivery']['address'] = {'text': order.data['contact_address']}
        # order_payload['delivery']['cost'] = ...


    ua_items = []
    for i in items:
        # For RetailCRM:
        item = {}
        order_payload['items'].append(item)
        item['offer'] = {'id': i['selected_offer_id']}
        if i['from_kit']:
            item['initialPrice'] = float(i['sum']) / i['count'] # XXX кривая цена, зато правильная сумма.
            item['priceType'] = {'code': 'null'}
        else:
            item['priceType'] = {'code': 'discount-retail' if i['discount_price'] else 'base'}

        item['quantity'] = i['count']
        #
        # For Universal Analytics:
        # see https://www.retailcrm.ru/docs/Users/GoogleAnalytics#settings_ga_code
        ua_i = {}
        ua_items.append(ua_i)
        # ID транзакции
        ua_i['id'] = order.id
        # Название товара
        ua_i['name'] = i['name']
        # Артикул или SKU
        ua_i['sku'] = i['selected_offer_id']
        # Стоимость товара
        if i['from_kit']:
            ua_i['price'] = item['initialPrice']
        else:
            ua_i['price'] = (i.get('discount_price') or i['price'])
        # Количество товара
        ua_i['quantity'] = i['count']

    url = "{}{}".format(BASE_API_URL, '/orders/create')

    r = requests.post(url, data={
        'apiKey': settings.RETAILCRM_API_SECRET,
        'site': SHOP_ID,
        'order': json.dumps(order_payload),
    })

    process_api_error(r)
    r_data = r.json()
    assert r_data['success'], r_data

    Order.objects.filter(id=order.id).update(
        sent_to_retailcrm=True,
        retailcrm_order_id=r_data['id'],
    )
    return {
        'order_id': r_data['id'],
        'ua_items': ua_items,
    }



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def op_days(request):
    qs_days = OperationalDay.objects.filter(
        day__gte=date.today()-timedelta(days=60),
        day__lte=date.today()+timedelta(days=1000),
    ).order_by('day')
    all_days = []
    for d in qs_days:
        all_days.append({'day': d.day, 'status': d.day_type})
        
    return Response([{
        'day': d['day'].isoformat(),
        'status': d['status'],
    } for d in all_days], status.HTTP_200_OK)


@transaction.atomic()
@api_view(['PUT', 'DELETE'])
@permission_classes([permissions.IsAdminUser])
def op_days_status(request, day, day_status):
    date = datetime.strptime(day, '%Y-%m-%d').date()
    try:
        od = OperationalDay.objects.get(day=date)
    except OperationalDay.DoesNotExist:
        od = None
        
    if request.method == 'PUT':
        if od is None:
            od, created = OperationalDay.objects.get_or_create(day=date)
            od.day_type = day_status
            od.save()
        else:
            OperationalDay.objects.filter(day=date).update(day_type=day_status)
        if day_status == 'closed':
            # mark previous days opened
            the_day = date - timedelta(days=1)
            while True:
                if the_day < date - timedelta(days=10):
                    break
                
                if not OperationalDay.objects.filter(day=the_day).exists():
                    new_d, created = OperationalDay.objects.get_or_create(day=the_day)
                    new_d.day_type='open'
                    new_d.save()
                    the_day = the_day - timedelta(days=1)
                else:
                    break
    if request.method == 'DELETE':
        if od is not None:
            od.delete()
            od = None
    return Response(
        {
            'day': date.isoformat(),
            'status': 'maybe-open' if od is None else od.day_type,
        },
        status.HTTP_200_OK)
