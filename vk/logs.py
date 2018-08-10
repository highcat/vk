# -*- coding: utf-8 -*-
"""
Please import all loggers from this file,
so occasional mistakes with log names will never happen.
"""

import logging

log = logging.getLogger()
email_log = logging.getLogger('user_emails')
ms_log = logging.getLogger('misc_scripts')

apns_log = logging.getLogger('apns')
