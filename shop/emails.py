# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def send(rcpt, subject, plain_message, body=None, attachments=None):
    msg = EmailMultiAlternatives(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [rcpt])
    if body:
        msg.attach_alternative(body, "text/html")
    if attachments:
        for a in attachments:
            msg.attach(a['file_name'], a['content'], a['mime_type'])
    msg.send()