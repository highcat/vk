# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-11-12 12:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0012_auto_20181112_1516'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='active',
            field=models.BooleanField(default=True, verbose_name='\u0410\u043a\u0442\u0438\u0432\u0435\u043d'),
        ),
    ]