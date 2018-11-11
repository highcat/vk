# -*- coding: utf-8 -*-
from rest_framework import serializers
from shop.models import Store


class StoreSerializes(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Store
        fields = [
            'retailcrm_slug',
            'name',
            'cart_name',
            'address',
            'work_hours',
        ]
