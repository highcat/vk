# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from django.conf import settings
from django.core.cache import caches
from .models import (
    Product, ProductImage, ProductKitItem, 
    Section,
    SitePreferences, 
    Order,
    Store,
    Article,
    PromoCode, AutoPromoCode,
    TelegramBot, TelegramBotRecipient,
    ContentImage,
)
from django.contrib.sites.models import Site
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage

from adminsortable2.admin import SortableInlineAdminMixin
from ajax_select.fields import AutoCompleteSelectField, AutoCompleteSelectMultipleField
from shop.widgets import HtmlEditor

admin.site.unregister(Site)


class ProductForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        exclude = ('slug',)

    description_html = forms.CharField(
        widget=HtmlEditor(attrs={'style': 'width: 90%; height: 100%;'}),
        required=False,
        label=u"HTML страницы продукта",
        help_text=u"HTML будет вставлен как есть."
    )
    page_title = forms.CharField(
        required=False, widget=forms.TextInput(attrs={'size': '100'}),
        label="Page title",
    )
    page_description = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'style': 'width: 50em; height:6em;'}),
        label="Мета-тег description на странице",
    )
    page_keywords = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'style': 'width: 50em; height:6em;'}),
        label="Мета-тег keywords на странице",
    )

    # скрытое поле, форсируем значение для каждой таблицы
    is_product_kit = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def clean_is_product_kit(self):
        """Force false for product"""
        return False


class ProductKitForm(ProductForm):
    def clean_is_product_kit(self):
        return True


class ProductOrKitSelectorForm(ProductForm):
    is_product_kit = forms.BooleanField( # Видимое
        required=False,
        label="Является набором",
        help_text=u"НЕ ПЕРЕКЛЮЧАТЬ БЕЗ НЕОБХОДИМОСТИ! Переносит товар в таблицу 'наборы', это удалит закупочную цену, и остатки в RetailCRM!"
    )
    def clean_is_product_kit(self):
        return self.cleaned_data['is_product_kit']


class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductImage


class ProductKitItemForm(forms.ModelForm):
    class Meta:
        model = ProductKitItem
        exclude = []
    product = AutoCompleteSelectField('product', label="", help_text=u"Поиск по названию", required=True)


from django.utils.safestring import mark_safe
class ProductKitItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductKitItem
    form = ProductKitItemForm
    fk_name = 'kit'
    readonly_fields = ('count_available',)
    def count_available(self, obj):
        left = obj.product.count_available
        packs_left = obj.product.count_available / obj.count if obj.count > 0 else float('inf')
        if packs_left == 0:
            return mark_safe(u'<span style="background-color: red; padding: 10px;">{} шт: НЕТ В НАЛИЧИИ</span>'.format(left))
        if packs_left < 4:
            return mark_safe(u'<span style="background-color: yellow; padding: 10px;">{} шт: заканчивается</span>'.format(left))
        if packs_left == float('inf'):
            return mark_safe(u'<span style="background-color: #ff7cf7; padding: 10px;">ноль продуктов в наборе???</span>'.format(left))
        return mark_safe(u'<span style="background-color: lightgreen; padding: 10px;">{} шт на складе</span>'.format(left))
            


class ProductAdmin_Base(admin.ModelAdmin):
    inlines = [
        ProductImageInline,
        ProductKitItemInline,
    ]
    form = ProductForm
    model = Product
    exclude = ('slug',)
    fields = (
        # sorted by usage frequency
        'retailcrm_link',
        # 
        'short_name',
        'preview',
        # 
        'preorder',
        'best_before_1',
        'best_before_2',
        'is_new',
        # 
        'article',
        # 
        'short_info',
        'info2',
        'hashtags',
        'exclude_from_search',
        'search_text',
        'overlay_image',
        #
        'is_market_test',
        #
        'page_title',
        'page_description',
        'page_keywords',
        #       
        'description_html',
        #
        'retailcrm_id',
        'price',
        'discount_price',
        'in_stock',
        'count_available',
        #
        'is_product_kit',
    )
    readonly_fields = (
        'retailcrm_link',
        'retailcrm_id',
        'short_name', # берётся из CRM
        'short_info', # берётся из CRM
        'info2', # берётся из CRM        
        'article',
        'price',
        'discount_price',
        'in_stock',
        'count_available',
    )
    list_display = (
        lambda o: u'{} - {}'.format(o.short_name, o.short_info),
        'article',
        'info2',
        'hashtags',
        'exclude_from_search',
        'search_text',
        'retailcrm_link',
        'is_market_test',
        'price',
        'discount_price',
        'in_stock',
        'is_new',
    )
    search_fields = ['short_name', 'short_info', 'info2', 'article']
    class Media:
        css = {
             'all': ('css/admin.css?v=1',)
        }

    def retailcrm_link(self, instance):
        if not instance.retailcrm_id:
            return mark_safe(u'<span style="color: red;">НЕТ В CRM</span>')
        return mark_safe(u'<a href="https://{}.retailcrm.ru/products/{}/edit">открыть в retailcrm</a>'.format(
            settings.RETAILCRM_ACCOUNT_NAME,
            instance.retailcrm_id,
        ))


class ProductAdmin_Normal(ProductAdmin_Base):
    inlines = [
        ProductImageInline,
    ]

    def get_queryset(self, request): # TODO should be get_queryset; deprecated since Django 1.6
        return (
            super(ProductAdmin_Normal, self)
            .get_queryset(request)
            .filter(is_product_kit=False)
        )


class ProductKitModelProxy(Product):
    class Meta:
        proxy = True
        verbose_name = u"Набор"
        verbose_name_plural = u"Наборы"


class ProductAdmin_Kits(ProductAdmin_Base):
    form = ProductKitForm
    readonly_fields = ProductAdmin_Base.readonly_fields + (
        'is_market_test', # this calculated automatically
    )
    inlines = [
        ProductImageInline,
        ProductKitItemInline,
    ]
    def get_queryset(self, request): # TODO should be get_queryset; deprecated since Django 1.6
        return (
            super(ProductAdmin_Kits, self)
            .get_queryset(request)
            .filter(is_product_kit=True)
        )


class ProductOrKitSelectorModelProxy(Product):
    class Meta:
        proxy = True
        verbose_name = u"Товар или Набор"
        verbose_name_plural = u"Товар ←→ Набор"
class ProductOrKitSelectorAdmin(ProductAdmin_Base):
    form = ProductOrKitSelectorForm
    inlines = []
    fields = (
        'is_product_kit', # the only editable field
        # 
        'retailcrm_link',
        'article',
        'short_name',
        'short_info',
    )
    readonly_fields = (
        'retailcrm_link',
        'article',
        'short_name',
        'short_info',
    )
    list_display = (
        lambda o: u'{} - {}'.format(o.short_name, o.short_info),
        'is_product_kit',
        'retailcrm_link',
    )

admin.site.register(Product, ProductAdmin_Normal)
admin.site.register(ProductKitModelProxy, ProductAdmin_Kits)
admin.site.register(ProductOrKitSelectorModelProxy, ProductOrKitSelectorAdmin)


class StoreAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'address',
        'work_hours',
        'retailcrm_slug',
        'priority_for_courier',
        'priority_for_post',
        'has_kit_packer',
    )

admin.site.register(Store, StoreAdmin)



class SectionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    class Media:
        css = {
             'all': ('css/admin.css?v=1',)
        }
admin.site.register(Section, SectionAdmin)


class PreferencesForm(forms.ModelForm):
    class Meta:
        model = SitePreferences
        exclude = []

    product_description_template = forms.CharField(
        widget=HtmlEditor(attrs={'style': 'width: 90%; height: 100%;'}),
        required=False,
        label=u"Шаблон описания продукта",
        help_text=u"Копируется автоматически при создании нового товара через CRM",
    )

    def clean(self):
        cache = caches['default']
        cache.delete('site_prefs')
        return self.cleaned_data


class PreferencesAdminCustom(admin.ModelAdmin):
    form = PreferencesForm
    class Media:
        css = {
             'all': ('css/admin.css?v=1',)
        }
admin.site.register(SitePreferences, PreferencesAdminCustom)


class FlatPageCustomizedForm(FlatpageForm):
    class Meta:
        model = FlatPage
        fields = ('url', 'title', 'content', 'template_name')

    content = forms.CharField(
        widget=HtmlEditor(attrs={'style': 'width: 90%; height: 100%;'}),
        label=u"HTML страницы",
        help_text=u"Будет вставлен как есть. Аккуратнее, этим кодом можно сломать страницу."
    )


class FlatPageCustomizedAdmin(FlatPageAdmin):
    form = FlatPageCustomizedForm
    fieldsets = (
        (None, {'fields': ('url', 'title', 'content', 'template_name', 'sites')}),
    )
    list_display = ('url', 'title',)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "sites":
            kwargs["initial"] = [Site.objects.get_current()]
        return super(FlatPageAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
             'all': ('css/admin.css?v=1',)
        }

admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageCustomizedAdmin)



class OrderAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'email_to_managers', 'sent_to_retailcrm', 'retailcrm_order_id', 'sent_to_telegram_bot')
    date_hierarchy = 'created_at'
    readonly_fields = ('data', 'email_to_managers', 'sent_to_telegram_bot', 'sent_to_retailcrm', 'retailcrm_order_id')

admin.site.register(Order, OrderAdmin)


from djcelery.models import (TaskState, WorkerState, PeriodicTask, IntervalSchedule, CrontabSchedule)
admin.site.unregister(TaskState)
admin.site.unregister(WorkerState)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(PeriodicTask)




class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        exclude = ['slug']

    html = forms.CharField(
        widget=HtmlEditor(attrs={'style': 'width: 90%; height: 100%;'}),        
        required=False,
        label=u"HTML статьи.",
        help_text=u"Будет вставлен как есть. Аккуратнее, этим кодом можно сломать страницу."
    )


class ArticleAdmin(admin.ModelAdmin):
    form = ArticleForm
    model = Article
    list_display = ('title', 'created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Article, ArticleAdmin)


class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        exclude = []

    def clean_variable_discount(self):
        p = self.cleaned_data.get('variable_discount')
        if p < 0 or p > 90:
            raise forms.ValidationError(u'Неверная скидка в процентах')
        return p
    def clean_code(self):
        code = self.cleaned_data.get('code')
        exists = False
        for pc in PromoCode.objects.filter(code__iexact=code).exclude(id=self.instance.id):
            if pc.is_active():
                exists = True
        for pc in AutoPromoCode.objects.filter(code__iexact=code):
            if pc.is_active():
                exists = True
        if exists and self.instance.is_active():
            raise forms.ValidationError(u'Такой код уже есть у действующей акции')
        return code


class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'active',
        'active_message',
        'variable_discount',
        'fixed_discount',
        'start_time',
        'end_time',
        'usage_count',
        'used_times',
        )
    ordering = ('-created_at',)
    form = PromoCodeForm
    model = PromoCode
    readonly_fields = ('used_times',)
    def active(self, instance):
        return u'*** АКТИВНА ***' if instance.is_active() else ''
    def active_message(self, instance):
        return instance.is_active_and_msg()[1]

admin.site.register(PromoCode, PromoCodeAdmin)


class AutoPromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'session_key',
        'name',
        'active',
        'active_message',
        'variable_discount',
        'fixed_discount',
        'start_time',
        'end_time',
        'usage_count',
        'used_times',
        )
    ordering = ('-created_at',)
    readonly_fields = list_display
    model = AutoPromoCode
    def active(self, instance):
        return u'*** АКТИВНА ***' if instance.is_active() else ''
    def active_message(self, instance):
        return instance.is_active_and_msg()[1]

admin.site.register(AutoPromoCode, AutoPromoCodeAdmin)


admin.site.register(TelegramBot)
admin.site.register(TelegramBotRecipient)


admin.site.register(ContentImage)
## TODO: image preview; somehow it won't load utils.templatetags, strange import error
# from utils.templatetags.static_versioning image_resize
# class ContentImageAdmin(admin.ModelAdmin):
#     list_display = ('preview', 'image',)
#     def preview(self, obj):
#         return mark_safe(u'<img src="{}" style="width:50px" />'.format(
#             static_versioning.image_resize(obj.img.url, 50)
#         ))
# admin.site.register(ContentImage, ContentImageAdmin)
