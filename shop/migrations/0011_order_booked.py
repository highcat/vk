# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-11-11 20:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0010_store_cart_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='booked',
            field=models.BooleanField(default=False),
        ),
    ]
