# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.db.models import F, Q
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.sites.models import Site
from django.contrib.postgres.fields import JSONField
from sortedm2m.fields import SortedManyToManyField
from transliterate import translit
import image_compression


class Product(models.Model):
    is_product_kit = models.BooleanField(
        default=False,
        verbose_name=u"Является набором",
        help_text=u"НЕ ПЕРЕКЛЮЧАТЬ БЕЗ НЕОБХОДИМОСТИ! Переносит товар в таблицу 'наборы', это удалит закупочную цену, и остатки в RetailCRM!",
    )
    best_before_1 = models.DateField(null=True, blank=True, verbose_name=u"Годен до", help_text="старая партия")
    best_before_2 = models.DateField(null=True, blank=True, verbose_name=u"Годен до (новая)", help_text="новая партия")

    article = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name=u"Артикул",
    )
    retailcrm_id = models.IntegerField(null=True, unique=True, blank=True, verbose_name=u"ID из RetailCRM")

    short_name = models.CharField(max_length=300, verbose_name=u"Имя", help_text="основное имя, для витрины")
    short_info = models.CharField(max_length=100)
    search_text = models.CharField(max_length=1000, blank=True, help_text="Дополнительный текст для поиска.")
    exclude_from_search = models.BooleanField(default=False, help_text="Исключить из поиска.")
    hashtags = models.CharField(max_length=1000, blank=True, help_text="Хэштэги, через запятую.")

    info2 = models.CharField(max_length=300, blank=True, verbose_name=u"Инфо 2")
    slug = models.CharField(max_length=40, blank=True)
    image_original = models.ImageField(upload_to="product-previews")
    image_compressed = models.ImageField(upload_to="product-previews-compressed", blank=True, help_text="Сжимается автоматически на сервере")
    image_compressed_with_tinypng = models.BooleanField(
        default=False,
        help_text="Означает, что картинка сконвертирована через TinyPNG, т.е. лучшего качества. Если TinyPNG был недоступен, конверсию делал наш сервер."
    )

    price = models.IntegerField(default=0)
    discount_price = models.IntegerField(null=True, blank=True)

    in_stock = models.BooleanField(default=True)
    count_available = models.PositiveIntegerField(default=0, verbose_name=u"Кол-во доступное для заказа")

    preorder = models.DateField(null=True, blank=True, verbose_name=u"Предзаказ")
    is_market_test = models.BooleanField(default=False, verbose_name=u"Тест рынка", help_text=u"Тест рынка, либо товар который мы закупаем оперативно. Наличие на складе для такого товара не учитывается!")
    is_new = models.BooleanField(default=True, verbose_name=u"Новинка")
    overlay_image = models.ImageField(upload_to="product-overlays", blank=True, verbose_name=u"Картинка поверх")

    page_title = models.CharField(max_length=1000, verbose_name=u"Тег title на странице", blank=True)
    page_description = models.TextField(verbose_name=u"Мета-тег description на странице", blank=True)
    page_keywords = models.TextField(verbose_name=u"Мета-тег keywords на странице", blank=True)

    description_html = models.TextField(blank=True)

    class Meta:
        verbose_name = u'Товар'
        verbose_name_plural = u'Товары'

    def save(self, **kwargs):
        # update slug
        self.slug = slugify(translit(self.short_name, 'ru', reversed=True), allow_unicode=False)[:40]
        # update is_market_test
        if self.is_product_kit and self.id:
            self.is_market_test = self.kit_items.filter(product__is_market_test=True).exists()
        # update cropped image
        old = None
        if self.id:
            old = Product.objects.get(pk=self.id)
        image_compression.convert_for_product(self, old)
        super(Product, self).save(**kwargs)

    def __unicode__(self):
        return u'{} - {}'.format(self.short_name, self.short_info)

    def get_count_by_stores(self):
        store_dict = dict((s.retailcrm_slug, {'count': 0, 'store': s}) for s in Store.objects.order_by('retailcrm_slug'))
        if not self.is_product_kit:
            for offer in self.retailcrm_offers.prefetch_related('counts_in_stores', 'counts_in_stores__store').all():
                for oc in offer.counts_in_stores.all():
                    store_dict[oc.store.retailcrm_slug]['count'] += oc.count
        else:
            for s, count in store_dict.iteritems():
                store_dict[s]['count'] = ProductKitMakeableCount.objects.get(product=self, store__retailcrm_slug=s).count
        return {
            'total': sum(map(lambda x: x[1]['count'], store_dict.items())),
            'stores': sorted(store_dict.items(), key=lambda x: x[0]),
        }


class ProductOffer(models.Model):
    """Product offers from RetailCRM; 
    Needed to store IDs.
    """
    product = models.ForeignKey(Product, related_name="retailcrm_offers")
    offer_id = models.IntegerField() # FIXME retailcrm_offer_id


class Store(models.Model):
    name = models.CharField(max_length=200, verbose_name=u"Название")
    cart_name = models.CharField(max_length=200, verbose_name=u"Короткое название для корзины")
    address = models.CharField(max_length=500, verbose_name=u"Адрес")
    work_hours = models.CharField(max_length=500, verbose_name=u"Часы работы")
    retailcrm_slug = models.CharField(max_length=200)
    priority_for_courier = models.FloatField(default=50, verbose_name=u"Приоритет для доставки курьером")
    priority_for_post = models.FloatField(default=50, verbose_name=u"Приоритет для отправки почтой")
    has_kit_packer = models.BooleanField(default=False, verbose_name=u"Есть сотрудник, упаковывающий наборы")
    def __unicode__(self):
        return u'{} [{}]'.format(self.name, self.retailcrm_slug)
    class Meta:
        verbose_name = u'Склад'
        verbose_name_plural = u'Склады'
        ordering = ['retailcrm_slug']


class ProductKitMakeableCount(models.Model):
    product = models.ForeignKey(Product, related_name='counts_makeable_in_stores')
    store = models.ForeignKey(Store)
    count = models.PositiveIntegerField()


class ProductOfferCount(models.Model):
    offer = models.ForeignKey(ProductOffer, related_name='counts_in_stores')
    store = models.ForeignKey(Store)
    count = models.PositiveIntegerField()


class ProductImage(models.Model):
    product = models.ForeignKey(Product)
    image = models.ImageField(upload_to="product-images")
    descripton = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    class Meta:
        verbose_name = u'Картинка Товара'
        verbose_name_plural = u'Картинки Товаров'
        ordering = ['order']


class ProductKitItem(models.Model):
    kit = models.ForeignKey(Product, related_name="kit_items")
    product = models.ForeignKey(Product, related_name="in_kits")
    count = models.PositiveIntegerField(default=1)

    order = models.IntegerField(default=0)
    class Meta:
        ordering = ['order']

    def get_count_on_store(self, store):
        if not store.has_kit_packer:
            return 0
        return sum([oc.count for oc in  ProductOfferCount.objects.filter(
            offer__product=self.product,
            store=store,
        )])
        


class Section(models.Model):
    name = models.CharField(max_length=15)
    slug = models.CharField(max_length=15, unique=True)
    header_id = models.CharField(max_length=20)

    page_title = models.CharField(max_length=1000, verbose_name=u"Тег title", blank=True)
    page_description = models.TextField(verbose_name=u"Мета-тег description", blank=True)
    page_keywords = models.TextField(verbose_name=u"Мета-тег keywords", blank=True)

    products = SortedManyToManyField(Product, blank=True)
    class Meta:
        verbose_name = u'Раздел'
        verbose_name_plural = u'Разделы'



### Site preferences
class SitePreferences(models.Model):
    class Meta:
        verbose_name = u"Настройки сайта"
        verbose_name_plural = u"Настройки сайта"
    def __unicode__(self):
        return self.site.name
    site = models.ForeignKey(Site)

    main_page_redirect = models.CharField(max_length=500, default='/section/hits/')

    callback_button = models.CharField(
        max_length=100,
        blank=True,
        choices=(
            ('', u'Без кнопки'),
            ('zadarma-01', 'zadarma-01'),
            ('zadarma-02', 'zadarma-02'),
            ('zadarma-03', 'zadarma-03'),
        ),
        verbose_name=u"Кнопка обратного звонка",
    )

    product_description_template = models.TextField(
        blank=True,
        verbose_name=u"Шаблон описания продукта",
        help_text=u"Копируется автоматически при создании нового товара через CRM",
    )


class Order(models.Model):
    class Meta:
        verbose_name = u"Заказ"
        verbose_name_plural = u"Заказы"

    data = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    booked = models.BooleanField(default=False)
    
    email_to_managers = models.BooleanField(default=False)
    email_to_customer = models.BooleanField(default=False)
    sent_to_telegram_bot = models.BooleanField(default=False)
    sent_to_retailcrm = models.BooleanField(default=False)
    retailcrm_order_id = models.IntegerField(null=True)


class OperationalDay(models.Model):
    day = models.DateField()
    day_type = models.CharField(max_length=10, choices=(('normal', 'normal'), ('day-off', 'day-off')))


def get_default_now():
    return timezone.now()

class Article(models.Model):
    enabled = models.BooleanField(verbose_name=u"Опубликована", default=True)
    created_at = models.DateTimeField(default=get_default_now, verbose_name=u"Дата создания или публикации")

    title = models.CharField(max_length=100, help_text=u"Заголовок и тег title")
    page_description = models.TextField(verbose_name=u"Мета-тег description", blank=True)
    page_keywords = models.TextField(verbose_name=u"Мета-тег keywords", blank=True)

    image = models.ImageField(upload_to="articles", blank=True)
    html = models.TextField(help_text=u"Загружайте картинки для контента через <a href=''>эту страницу</a>; Используйте специальные URL вида /media/resize/<ширина>/<остальное>.jpg для изменения размера картинки.")

    slug = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = u"Статья"
        verbose_name_plural = u"Статьи"

    def save(self, **kwargs):
        self.slug = slugify(translit(self.title, 'ru', reversed=True), allow_unicode=False)[:100]
        super(Article, self).save(**kwargs)


class PromoCodeActiveManager(models.Manager):
    def get_queryset(self):
        return (
            super(PromoCodeActiveManager, self)
            .get_queryset()
            .filter(Q(start_time__isnull=True) | Q(start_time__lte=timezone.now()))
            .filter(Q(end_time__isnull=True) | Q(end_time__gte=timezone.now()))
            .filter(Q(usage_count=0) | Q(usage_count__gte=F('used_times')))
        )

class PromoCode(models.Model):
    objects = models.Manager()
    objects_active = PromoCodeActiveManager()

    code = models.CharField(max_length=50, help_text=u"Разрешается использовать тот же код, если старая акция уже не активна.")

    name = models.CharField(blank=True, max_length=100, verbose_name=u"Название скидки/акции", help_text="Будет показано клиенту. Можно оставить пустым.")
    created_at = models.DateTimeField(auto_now_add=True)

    variable_discount = models.PositiveIntegerField(default=0, verbose_name=u"Скидка в %")
    fixed_discount = models.PositiveIntegerField(default=0, verbose_name=u"Скидка в рублях")

    start_time = models.DateTimeField(null=True, blank=True, verbose_name=u"Действие начинается с")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=u"Действие заканчивается в")
    usage_count = models.PositiveIntegerField(default=0, verbose_name=u"Макс кол-во использований", help_text="0 значит бесконечно")

    used_times = models.PositiveIntegerField(default=0, verbose_name="Сколько раз использовано")

    def is_active_and_msg(self):
        if self.start_time and self.start_time > timezone.now():
            return False, u'Код ещё не начал действовать'
        if self.end_time and self.end_time < timezone.now():
            return False, u'Срок действия кода истёк'
        if self.usage_count > 1 and self.usage_count <= self.used_times:
            return False, u'Код уже использован все {} раз(а)'.format(self.usage_count)
        if self.usage_count == 1 and self.used_times >= 1:
            return False, u'Код уже использован.'
        return True, u''

    def is_active(self):
        return self.is_active_and_msg()[0]

    class Meta:
        verbose_name = u"Промо-Код"
        verbose_name_plural = u"Промо-Коды"


class AutoPromoCode(models.Model):
    u"""
    Полностью аналогичен PromoCode, кроме идентификатора пользователя.
    FIXME лучше использвать одну таблицу, а в админке фильтровать.
    """
    objects = models.Manager()
    objects_active = PromoCodeActiveManager()

    name = models.CharField(max_length=100, verbose_name=u"Название скидки")
    code = models.CharField(max_length=50, verbose_name=u"Код")
    created_at = models.DateTimeField(auto_now_add=True)

    variable_discount = models.PositiveIntegerField(default=0, verbose_name=u"Скидка в %")
    fixed_discount = models.PositiveIntegerField(default=0, verbose_name=u"Скидка в рублях")

    start_time = models.DateTimeField(null=True, blank=True, verbose_name=u"Действие начинается с")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=u"Действие заканчивается в")
    usage_count = models.PositiveIntegerField(default=0, verbose_name=u"Макс кол-во использований", help_text="0 значит бесконечно")

    used_times = models.PositiveIntegerField(default=0, verbose_name="Сколько раз использовано")
    session_key = models.CharField(max_length=200, verbose_name=u"Ключ сессии пользователя")

    def is_active_and_msg(self):
        if self.start_time and self.start_time < timezone.now():
            return False, u'Код ещё не начал действовать'
        if self.end_time and self.end_time < timezone.now():
            return False, u'Срок действия кода истёк'
        if self.usage_count > 1 and self.usage_count <= self.used_times:
            return False, u'Код уже использован все {} раз(а)'.format(self.usage_count)
        if self.usage_count == 1 and self.used_times >= 1:
            return False, u'Код уже использован.'
        return True, u''

    def is_active(self):
        return self.is_active_and_msg()[0]


    class Meta:
        verbose_name = u"Автоматический промо-код"
        verbose_name_plural = u"Автоматические промо-коды"



class TelegramBot(models.Model):
    url = models.CharField(max_length=100)
    api_key = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    updates_offset = models.IntegerField(default=0)

class TelegramBotRecipient(models.Model):
    bot = models.ForeignKey(TelegramBot)
    recipient_id = models.CharField(max_length=500, unique=True)
    authorized = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return u"{} - {}".format(
            self.username or (self.first_name or u'') + (self.last_name or u''),
            self.created_at,
        )

class ContentImage(models.Model):
    u"""Generic uploaded image, for any content"""
    class Meta:
        verbose_name = u"Картинка в контент"
        verbose_name_plural = u"Картинки в контент"

    image = models.ImageField(upload_to="content-img", help_text=u"""
    Этот URL можно использовать в любом месте сайта.
    <br>Не удаляй картинки без необходимости (не проверив контент).
    <br><br>Загружай картинку максимального размера!
    <br><br>Затем, используй специальные URL для ресайза картинки:
    <br>&nbsp;/media/resize/<ширина>/<остальное>.jpg
    <br>&nbsp;/media/resize/<ширина>x<высота>/<остальное>.jpg
    <br>&nbsp;/media/crop/<ширина>/<остальное>.jpg</li>
    <br>&nbsp;/media/crop/<ширина>x<высота>/<остальное>.jpg
    """)
    def __unicode__(self):
        return self.image.url
