# -*- coding: utf-8 -*-

"""
XXX
Бронирование проиходит отсроченно, хоть и непосредственно после создания заказа.
Проблема на будущее в том, что товарные предложения подбираются синхронно,
а бронирование делается - асинхронно.

При одновременных заказах возможны ошибки бронирования,
с которыми придётся разбираться оператору.
"""
from copy import deepcopy
from .models import Product, Store


def choose_offers(offer_counts, delivery_type, items):
    """Подобрать товарные предложения так, чтобы они были с нужного склада
    items - структура из api.py для отправки в RetailCRM
    offer_counts - словарик кол-ва на складе по offer_id и ID склада.
    """
    # Выбор основного склада
    if delivery_type.startswith('selfdelivery--'):
        # Самовывоз - по возможности склад, где товар уже есть
        shipment_store = Store.objects.get(retailcrm_slug=delivery_type[len('selfdelivery--'):])
    elif delivery_type == 'delivery-post':
        # Доставка - берём приоритетный для доставки почтой склад
        shipment_store = Store.objects.order_by('-priority_for_post')[0]
    else:
        # Доставка - берём приоритетный для доставки курьером склад.
        # / --- TODO выбирать тот, где точно есть товар --- /
        shipment_store = Store.objects.order_by('-priority_for_courier')[0]


    # Decide which offers to use; split if necessary
    items = deepcopy(items)
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
    return {
        'items': items,
        'shipment_store': shipment_store,
    }


def book(order):
    # *** Блок Логистики ***
    # См https://help.retailcrm.ru/Users/Logistics
    # Как выбирается склад отгрузки:
    # 1. Самовывоз: склад отгрузки = место самовывоза.
    # 1.1. Оптимизация: подбираем offers товара именно с этого склада.
    # 2. Курьер: склад отгрузки = то, где больше товара
    # 2.1. Где есть весь товар (с учётом offers)
    # 2.2. Где больше всего товара.  (с учётом offers)
    # 2.3. Идеал: где больше всего товара по объёму и массе, а также ближе всего к клиенту.
    # 
    # 3. Доставка почтой - отгрузка и бронь всегда с Вкусняна. 
    # 
    # 4. Создать задачу на перенос товара - в RetailCRM, в Telegram.
    # if partial_shipment:
    #     '/api/v5/orders/combine' # ??? ручной выбор склада
    # else:
    #     order_payload['shipmentStore']

    pass
    # Order.objects.filter(id=order.id).update(booked=True)
