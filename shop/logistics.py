# -*- coding: utf-8 -*-


def book(order):
      # *** Блок Логистики ***
    # # См https://help.retailcrm.ru/Users/Logistics
    # # Как выбирается склад отгрузки:
    # # 1. Самовывоз: склад отгрузки = место самовывоза.
    # # 1.1. Оптимизация: подбираем offers товара именно с этого склада.
    # # 2. Курьер: склад отгрузки = то, где больше товара
    # # 2.1. Где есть весь товар (с учётом offers)
    # # 2.2. Где больше всего товара.  (с учётом offers)
    # # 2.3. Идеал: где больше всего товара по объёму и массе, а также ближе всего к клиенту.
    # # 
    # # 3. Создать задачу на перенос товара - в RetailCRM, в Telegram.
    # if partial_shipment:
    #     '/api/v5/orders/combine' # ??? ручной выбор склада
    # else:
    #     order_payload['shipmentStore']

    pass
    # Order.objects.filter(id=order.id).update(booked=True)
