# -*- coding: utf-8 -*-
from optparse import make_option
from django.core import management
from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

class Command(NoArgsCommand):
    """Change user passwords to '11' - for dev machines, used by `fab clone_db`."""
    option_list = (
        make_option('--apply', help='Apply changes',
                    action='store_true', default=False),
    ) + NoArgsCommand.option_list
    def handle_noargs(self, **options):
        if options.get('apply'):
            for u in User.objects.filter(is_superuser=True):
                u.set_password('11')
                print u
                u.save()
