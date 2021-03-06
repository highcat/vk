# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-11-05 17:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_productkitmakeablecount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productkitmakeablecount',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='counts_makeable_in_stores', to='shop.Product'),
        ),
    ]
