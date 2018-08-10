# -*- coding: utf-8 -*-
from locked_pidfile.django_management import single
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):
        from shop.tasks import telegram_bot_update_recipients
        telegram_bot_update_recipients()
