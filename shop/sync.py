# -*- coding: utf-8 -*-
import re
import requests
from pprint import pprint
from copy import copy, deepcopy
from django.db import transaction
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.utils.http import urlencode
from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

import json
import requests
from shop.utils import BASE_URL, BASE_URL_V5, SHOP_ID
from shop.utils import process_api_error
from time import sleep
from vk.logs import log

from .models import (
    Product, Section, Order, Article, ProductOffer,
    ProductOfferCount, Store,
)
from .utils import GET_SITE_PREFS
from .utils import paginate_retailcrm


def full_sync():
    sync_new_items()
    sync_fields()
    data = collect_sync_data()
    sync_prices(data['common'], data['plist_f'])
    # sync_images() # enable on new version
    fix_offers()

    fix_preorders() # удалить старые предзаказы
    update_kits_is_market_test()



def collect_sync_data():
    """FIXME уже синхронизует. Переименовать, упростить"""
    plist_vk = dict((p.id, p) for p in Product.objects.all())
    plist_vk_by_new_id = dict(
        (p.retailcrm_id or "(no retailcrm ID):{}".format(p.id), p)
        for p in Product.objects.all()
    )

    # see https://www.retailcrm.ru/docs/Developers/ApiRules

    plist_f = {}
    for data in paginate_retailcrm('/store/products', {
        'limit': '100',
    }):
        for p in data['products']:
            # assert p['minPrice'] == p['maxPrice']

            # get actual retail price
            offer = p['offers'][0]
            all_prices = sorted(
                filter(lambda p: p['priceType']=='base', offer['prices']),
                key=lambda p: p['ordering']
            )
            if len(all_prices):
                price = all_prices[0]['price']
            else:
                price = 0

            l_discount_price = sorted(
                filter(lambda p: p['priceType']=='discount-retail', offer['prices']),
                key=lambda p: p['ordering']
            )
            discount_price = None
            if len(l_discount_price):
                discount_price = l_discount_price[0]['price']
                
            p.get('imageUrl') # optional
            p.get('manufacturer') # optional, but needed
            plist_f[p['id']] = {
                'retailcrm_id': p['id'],
                'article': p.get('article', ''),
                'name': p['name'],
                'price': price,
                'discount_price': discount_price,
                # Возвращает сразу по всем складам, 'quantity' не фильтруется по магазину.
                # FIXME Использовать /api/v5/store/inventories: offers[][stores][][quantity]
                'count_available': p['quantity'] if p['active'] else 0,
                'offer_ids': [o['id'] for o in p['offers']],
            }
            # pprint(p)


    # Save count by stores
    store_dict = dict((s.retailcrm_slug, s) for s in Store.objects.all())
    for data in paginate_retailcrm('/store/inventories', {
        'filter[details]': '1',
        'filter[offerActive]': '1',            
        'limit': '250',
    }, base_url=BASE_URL_V5):
        for offer in data['offers']:
            product = ProductOffer.objects.get(offer_id=offer['id']).product
            all_stores = set(slug for slug, store in store_dict.items())
            # Existing stores - set quantity
            for store in offer['stores']:
                if product.is_product_kit:
                    continue
                all_stores.remove(store['store'])
                try:
                    store_dict[store['store']]
                except KeyError:
                    log.exception('Need to add store to website', extra={
                        'store': store['store'],
                        'product': product.short_name,
                    })
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
            # Stores not returned listed - zero quantity
            for s in all_stores:
                try:
                    oc = ProductOfferCount.objects.get(
                        offer__offer_id=offer['id'],
                        store=Store.objects.get(retailcrm_slug=s),
                    )
                except ProductOfferCount.DoesNotExist:
                    oc = ProductOfferCount(
                        offer=ProductOffer.objects.get(offer_id=offer['id']),
                        store=Store.objects.get(retailcrm_slug=s),
                    )
                oc.count = 0
                oc.save()
            

    common = set()
    vk_left = copy(plist_vk)
    f_left = copy(plist_f)
    for id, pf in plist_f.iteritems():
        vk_id_to_delete = None
        rcrm_id_to_add = None
        for vkl_id, vkl_obj in vk_left.iteritems():
            if vkl_obj.retailcrm_id == id:
                vk_id_to_delete = vkl_obj.id
                rcrm_id_to_add = vkl_obj.retailcrm_id
        if vk_id_to_delete:
            del vk_left[vk_id_to_delete]
            common.add(rcrm_id_to_add)
    for id, pvk in plist_vk.iteritems():
        if pvk.retailcrm_id in f_left:
            del f_left[pvk.retailcrm_id]

    return {
        'plist_vk': plist_vk,
        'plist_vk_by_new_id': plist_vk_by_new_id,
        'plist_f': plist_f,
        'common': common,
        'vk_left_set': vk_left.keys(),
        'f_left_set': f_left.keys(),
    }


def sync_prices(obj_ids, new_data):
    for id in obj_ids:
        # Update products
        Product.objects.filter(retailcrm_id=id).update(
            article=new_data[id]['article'],
            #
            price=new_data[id]['price'],
            discount_price=new_data[id]['discount_price'] or None,
            count_available=new_data[id]['count_available'],
            in_stock=True if new_data[id]['count_available'] > 0 else False,
        )
        p = Product.objects.get(retailcrm_id=id)
        # Create offers
        for offer_id in new_data[id]['offer_ids']:
            ProductOffer.objects.get_or_create(
                product=p, 
                offer_id=offer_id,
            )
        # delete old offers (removed by user from RetailCRM)
        (ProductOffer.objects
         .filter(product=p)
         .exclude(offer_id__in=new_data[id]['offer_ids'])
         .delete()
        )
    # [OLD] calculate counts of product kits
    for kit in Product.objects.filter(is_product_kit=True):
        max_count = 9999
        for ki in kit.kit_items.all():
            p = Product.objects.get(id=ki.product.id)
            available = p.count_available
            if p.preorder != None or p.is_market_test:
                available = 9999
            max_for_ki = available / ki.count
            if max_count > max_for_ki:
                max_count = max_for_ki
        Product.objects.filter(id=kit.id).update(
            count_available=max_count,
            in_stock=True if max_count > 0 else False,
        )
    # Calculate counts of product kits by store
    for store in Store.objects.all():
        for kit in Product.objects.filter(is_product_kit=True):
            max_count = 9999
            for ki in kit.kit_items.all():
                p = Product.objects.get(id=ki.product.id)
                available = p.count_available
                if p.preorder != None or p.is_market_test:
                    available = 9999
                max_for_ki = available / ki.get_count_on_store(store)
                if max_count > max_for_ki:
                    max_count = max_for_ki
            Product.objects.filter(id=kit.id).update(
                count_available=max_count,
                in_stock=True if max_count > 0 else False,
            )

    # Наборы: принудительно сбрасываем остатки и закупочные цены в CRM
    payload = []
    for kit in Product.objects.filter(is_product_kit=True):
        payload.append({
            'id': kit.retailcrm_offers.all()[0].offer_id,
            'stores': [{
                'code': store,
                'available': 9999,
                'purchasePrice': 0.01, # XXX проблема RetailCRM: 0 рублей выставить нельзя
            } for store in settings.RETAILCRM_ALL_STORES],
        })
    url = "{}{}".format(BASE_URL, '/store/inventories/upload')

    r = requests.post(url, data={
        'apiKey': settings.RETAILCRM_API_SECRET,
        'site': SHOP_ID,
        'offers': json.dumps(payload),
    })
    process_api_error(r, context_message=u"fixing kit count & purchasePrice")
    

def sync_images():
    qs_products = Product.objects.filter(preview='')
    products = dict((p.retailcrm_id, p) for p in qs_products) # FIXME optimize for memory!

    for data in paginate_retailcrm('/store/products', {
        'limit': '100',
    }, base_url=BASE_URL_V5):
        for p in data['products']:
            if p['id'] not in products:
                continue
            # TODO
            p['offers'][0]['images']


def sync_new_items():
    # 1. Добавить новые из RetailCRM
    products = dict((p.retailcrm_id, p) for p in Product.objects.all()) # FIXME optimize for memory!    
    in_retailcrm = set()
    for data in paginate_retailcrm('/store/products', {
        'limit': '100',
    }): # включая неактивные
        for p in data['products']:
            in_retailcrm.add(p['id'])
            if p['id'] not in products:
                crm_article = p.get('article', '')[:100]
                crm_name = p['name'].strip()
                print "adding new item", p['id']

                if crm_article and Product.objects.filter(article=crm_article).exists():
                    # mark duplicated article
                    crm_article = u'[ДУБЛЬ! id{}] {}'.format(p['id'], crm_article)[:100]

                names = parse_name(crm_name)
                obj = Product(
                    retailcrm_id=p['id'],
                    article=crm_article,
                    short_name=names['en'],
                    info2=names['info2'],
                    short_info=names['info'] or '',
                    description_html=GET_SITE_PREFS().product_description_template,
                )
                
                offer = p['offers'][0]
                if not obj.short_info:
                    obj.short_info = u'1 шт'
                    if offer.get('weight'):
                        obj.short_info += u' - {}гр'.format(offer['weight'])
                obj.save()
                products[obj.retailcrm_id] = obj

    # 2. Сделать удалённые неактивными (удалить retailcrm_id)
    for p in Product.objects.filter(retailcrm_id__isnull=False):
        if p.retailcrm_id not in in_retailcrm:
            print "unlinking product:", p.retailcrm_id
            # Recheck once more in CRM!
            url = "{}{}?{}".format(BASE_URL, '/store/products', urlencode([
                ('filter[ids][]', p.retailcrm_id),
                ('apiKey', settings.RETAILCRM_API_SECRET),
            ]))
            data = requests.get(url).json()
            if data['pagination']['totalCount'] == 0:
                # now unlink.
                Product.objects.filter(id=p.id).update(retailcrm_id=None)
                print "  DONE."
            else:
                print "  XXX should unlink, but still found in CRM! this shouldn't happen"


def sync_fields():
    # 1. Обновление имён
    for data in paginate_retailcrm('/store/products', {
        'limit': '100',            
    }): # включая неактивные
        for p in data['products']:
            names = parse_name(p['name'])
            Product.objects.filter(retailcrm_id=p['id']).update(
                short_name=names['en'],
                info2=names['info2'],
            )
            if names['info'] is not None:
                Product.objects.filter(retailcrm_id=p['id']).update(
                    short_info=names['info'],
                )
                


def parse_name(retailcrm_name):
    """Делим имя на название и инфо"""
    parts = retailcrm_name.split('/')
    
    en = parts[0]
    info = parts[1] if len(parts) > 1 else ''    
    info2 = parts[2] if len(parts) > 2 else ''

    MAX_LENGTH = 100
    # Trim
    en_trim = en[:MAX_LENGTH]
    if len(en_trim) < len(en):
        en_trim = en_trim[:MAX_LENGTH-1] + u'…'
    info_trim = info[:MAX_LENGTH]
    if len(info_trim) < len(info):
        info_trim = info_trim[:MAX_LENGTH-1] + u'…'
    info2_trim = info[:MAX_LENGTH]
    if len(info2_trim) < len(info):
        info2_trim = info2_trim[:MAX_LENGTH-1] + u'…'
    
    # Strip
    en = en_trim.strip()
    info = info_trim.strip()
    info2 = info2_trim.strip()
    
    return {
        'en': en,
        'info': info,
        'info2': info2,        
    }


def fix_offers():
    u"""Workaround for a bug:
    if a product has multiple offers, and "common price for all" is checked,
    it still thinks there's no price for 2nd, 3rd, etc offer.

    We just update it here.
    """
    for data in paginate_retailcrm('/store/products', {
        'limit': '100',            
    }):
        for p in data['products']:
            offers = p['offers']

            need_fix = False
            valid_price_list = deepcopy(offers[0]['prices'])
            # 0. нулевая цена должна существовать и равняться нулю
            null_prices = filter(lambda p: p['priceType'] == 'null', valid_price_list)
            if not null_prices:
                valid_price_list.append({'price': 0, 'priceType': 'null'})
            for np in null_prices:
                if np['price'] != 0:
                    np['price'] = 0
            # 1. цены должны быть одинаковыми
            for o in offers:
                # sort so they can match
                o['prices'].sort(key=lambda p: p['priceType'])
                valid_price_list.sort(key=lambda p: p['priceType'])
                # check
                if o['prices'] != valid_price_list:
                    need_fix = True

            # 2. Исправляем
            if need_fix:
                print 
                print 
                print 
                print "Prices not equal for:"
                pprint(offers)
                print "updating...."
                # prices[][prices][] array of objects (PriceUploadPricesInput)Цена торгового предложения
                # prices[][prices][][code] string Код типа цены
                # prices[][prices][][price] float Цена
                payload = []

                # XXX лишние цены не удаляются!
                for o in offers:
                    payload.append({
                        'id': o['id'],
                        'site': SHOP_ID,
                        'prices': [{'price': p['price'], 'code': p['priceType']} for p in valid_price_list],
                    })
                print "fixing with: "
                pprint(payload)
                url = "{}{}".format(BASE_URL, '/store/prices/upload')
                r = requests.post(url, data={
                    'apiKey': settings.RETAILCRM_API_SECRET,
                    'site': SHOP_ID,
                    'prices': json.dumps(payload),
                })
                if not process_api_error(r, silent=True, context_message=u"fixing offer prices"):
                    continue
                sleep(0.5) # FIXME consolidate instead, 250 max                    


def fix_preorders():
    (Product.objects
     .filter(preorder__lte=timezone.now().date())
     .update(preorder=None)
    )


def update_kits_is_market_test():
    for p in Product.objects.filter(is_product_kit=True):
        is_market_test = p.kit_items.filter(product__is_market_test=True).exists()
        Product.objects.filter(id=p.id).update(is_market_test=is_market_test)
