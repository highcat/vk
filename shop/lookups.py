# -*- coding: utf-8 -*-
from ajax_select import register, LookupChannel
from .models import Product
from django.db.models import Q

@register('product')
class MCQTestsLookup(LookupChannel):
    model = Product
    def get_query(self, q, request):
        out = []

        qs = self.model.objects.filter(
            # is_deleted=False,
        )
        out += list(
            qs.filter(
                Q(short_name__icontains=q) | Q(short_info__icontains=q),
                is_product_kit=False,
            ).order_by('short_name')[:10]
        )
        return out

    def format_item_display(self, item):
        label = u'{} | {}'.format(item.short_name, item.short_info)[:50]
        return u"<span class='tag'>%s</span>" % label

    def get_objects(self, ids):
        return self.model.objects.filter(is_product_kit=False, id__in=ids)
