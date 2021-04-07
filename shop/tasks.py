# -*- coding: utf-8 -*-
import json
from celery import task
from emailer import Email
from django.conf import settings
from .models import Order, Product, TelegramBot, TelegramBotRecipient
import requests
from vk.logs import log
from pprint import pprint
import telepot
from smtplib import SMTPAuthenticationError
from telepot import exception as telepot_exception
from . import logistics
from .emails import send as send_mail

TELEPOT_EXCEPTIONS_TO_SKIP = (
    telepot_exception.BotWasKickedError,
    telepot_exception.BotWasBlockedError,
    telepot_exception.TelegramError, # generic Telegram error FIXME?
)


@task(ignore_result=True)
def sync_order(order_id):
    order = Order.objects.get(id=order_id)
    data = order.data

    ## sent by mail
    email_subject = u'Заказ с Vkusnyan.ru на {price}р'.format(price=data['total_price'])
    email_body = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '), ensure_ascii=False)

    if not order.email_to_managers:
        try:
            for rcpt in settings.EMAIL_ORDERS_TO:
                send_mail(
                    rcpt=rcpt,
                    subject=email_subject,
                    plain_message=email_body,
                )
                Order.objects.filter(id=order.id).update(email_to_managers=True)
        except Exception:
            log.exception("Error sending order admins mailbox")

    if not order.email_to_customer and order.id > 3411:
        rcpt_client = data.get('contact_email')
        if not rcpt_client:
            Order.objects.filter(id=order.id).update(email_to_customer=True)
        else:
            try:
                send_mail(
                    rcpt=rcpt_client,
                    subject='Ваш заказ {} на Vkusnyan.ru'.format(order.retailcrm_order_id),
                    plain_message="""Вы создали заказ номер {order_id}\n\nна сумму {total} рублей.""".format(
                        order_id=order.retailcrm_order_id,
                        total=data.get('total_price'),
                    ),
                )
                Order.objects.filter(id=order.id).update(email_to_customer=True)
                print('sent_mail_to_customer - DONE')
            except Exception:
                log.exception("Error sending order client mailbox")

    ## sent by telegram bot
    if not order.sent_to_telegram_bot:
        try:        
            telegram_bot_update_recipients()
            telegram_bot_send(order)
            Order.objects.filter(id=order.id).update(sent_to_telegram_bot=True)
        except Exception:
            log.exception("Error sending order to telegram bot")



@task(ignore_result=True)
def book_order(order_id):
    order = Order.objects.get(id=order_id)
    logistics.book(order)



def telegram_bot_update_recipients():
    for bot_model in TelegramBot.objects.all():
        bot = telepot.Bot(bot_model.api_key.encode('utf-8')) # telepot's bug. If it's unicode, it won't accept unicode strings for sending.
        msgs = bot.getUpdates(offset=bot_model.updates_offset)
        offset = bot_model.updates_offset
        for m in msgs:
            offset = m['update_id'] + 1
            r, created = TelegramBotRecipient.objects.get_or_create(bot=bot_model, recipient_id=m['message']['from']['id'])
            if not r.authorized:
                if bot_model.password in m['message']['text'].strip():
                    r.authorized = True
                    r.first_name = m['message']['from'].get('first_name', '')
                    r.last_name = m['message']['from'].get('last_name', '')
                    r.username = m['message']['from'].get('username', '')
                    r.save()
                    if created:
                        bot.sendMessage(r.recipient_id, u"Авторизация успешна. Теперь вы будете получать заказы в этот чат.", parse_mode='markdown')
                else:
                    bot.sendMessage(r.recipient_id, u"Вы не авторизованы. Введите пароль.", parse_mode='markdown')
            if m['message'].get('text', '').strip() == 'unsubscribe':
                bot.sendMessage(r.recipient_id, u"Удаляю ваз из подписчиков...", parse_mode='markdown')
                r.delete()
                bot.sendMessage(r.recipient_id, u"Удаление успешно.", parse_mode='markdown')
                
        TelegramBot.objects.filter(id=bot_model.id).update(updates_offset=offset)



def telegram_bot_send(order):
    for bot_model in TelegramBot.objects.all():
        bot = telepot.Bot(bot_model.api_key.encode('utf-8')) # telepot's bug. If it's unicode, it won't accept unicode strings for sending.
        data = order.data
        msg = u'Заказ с Vkusnyan.ru на {price}р'.format(price=data['total_price'])
        for rec in TelegramBotRecipient.objects.filter(bot=bot_model):
            try:
                if rec.authorized:
                    bot.sendMessage(rec.recipient_id, msg, parse_mode='markdown')
                else:
                    bot.sendMessage(rec.recipient_id, u"Вы не авторизованы. Введите пароль.", parse_mode='markdown')
            except TELEPOT_EXCEPTIONS_TO_SKIP:
                log.exception("unable to send to recipient")



def telegram_bot_message(msg):
    for bot_model in TelegramBot.objects.all():
        bot = telepot.Bot(bot_model.api_key.encode('utf-8')) # telepot's bug. If it's unicode, it won't accept unicode strings for sending.
        for rec in TelegramBotRecipient.objects.filter(bot=bot_model):
            if rec.authorized:
                bot.sendMessage(rec.recipient_id, msg, parse_mode='markdown')
            else:
                bot.sendMessage(rec.recipient_id, u"Вы не авторизованы. Введите пароль.", parse_mode='markdown')
