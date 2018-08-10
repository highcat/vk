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

import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    @single(__name__)
    def handle(self, *args, **options):
        # p = Product.objects.get(product_id=ID)

        
