# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2020-02-18 14:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0017_auto_20200218_1611'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_compressed_with_tinypng',
            field=models.BooleanField(default=False, help_text='\u041e\u0437\u043d\u0430\u0447\u0430\u0435\u0442, \u0447\u0442\u043e \u043a\u0430\u0440\u0442\u0438\u043d\u043a\u0430 \u0441\u043a\u043e\u043d\u0432\u0435\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0430 \u0447\u0435\u0440\u0435\u0437 TinyPNG, \u0442.\u0435. \u043b\u0443\u0447\u0448\u0435\u0433\u043e \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u0430. \u0415\u0441\u043b\u0438 TinyPNG \u0431\u044b\u043b \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d, \u043a\u043e\u043d\u0432\u0435\u0440\u0441\u0438\u044e \u0434\u0435\u043b\u0430\u043b \u043d\u0430\u0448 \u0441\u0435\u0440\u0432\u0435\u0440.'),
        ),
    ]
