# -*- coding: utf-8 -*-
from locked_pidfile.django_management import single
from django.core.management.base import BaseCommand

from shop.sync import full_sync

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):
        full_sync()
