# -*- coding: utf-8 -*-
from django.core import management
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    """
    Migrate testing database. Useful for development, so you don't create it from scratch.
    """
    def handle_noargs(self, **options):
        management.call_command('migrate')
