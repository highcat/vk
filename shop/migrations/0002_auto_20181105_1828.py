# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-11-05 15:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductOfferCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField()),
                ('offer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.ProductOffer')),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('retailcrm_slug', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='productoffercount',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.Store'),
        ),
    ]
