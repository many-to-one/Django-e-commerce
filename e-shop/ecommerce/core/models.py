from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Category(models.Model):
    title = models.CharField(max_length=255,
                             verbose_name='Tytuł')
    slug = models.SlugField(max_length=255, verbose_name='Url', unique=True)
    photo = models.ImageField(upload_to='photo/%Y/%m/%d/',
                              verbose_name='Zdjęcie', blank=True)
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Czas dodania')
    updated_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Aktualizacja')

    class Meta:
        ordering = ['title']
        verbose_name = 'Kategoria'
        verbose_name_plural = 'Kategorii'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('category',
                       kwargs={'slug': self.slug})  # 'categoria' is url


class Item(models.Model):
    title = models.CharField(max_length=255,
                             verbose_name='Tytuł')
    short_title = models.CharField(
        max_length=22,
        null=True,
        verbose_name='Krótki tytuł',
    )
    slug = models.SlugField(max_length=255, verbose_name='Url', unique=True)
    price = models.FloatField(default=0,
                              verbose_name='Cena')
    discount_price = models.FloatField(blank=True, null=True,
                                       verbose_name='Cena ze zniżką')
    quantity = models.IntegerField(default=0)
    content = RichTextField(blank=True, verbose_name='Opis')
    photo = models.ImageField(upload_to='photo/%Y/%m/%d/',
                              verbose_name='Zdjęcie', blank=True)
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Czas dodania')
    updated_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Aktualizacja')
    is_published = models.BooleanField(default=True,
                                       verbose_name='Opublikowane')
    views = models.IntegerField(default=0, verbose_name='Liczba wyświetleń')
    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                                 verbose_name='Kategoria',
                                 related_name='posts')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Artykuł'
        verbose_name_plural = 'Artykuły'

    def __str__(self):
        return self.title

    def get_photo(self):
        return self.photo

    def get_absolute_url(self):
        return reverse('product',
                       kwargs={'slug': self.slug})  # 'product' is url

    def get_add_to_cart_url(self):
        return reverse('add_to_cart',
                       kwargs={'slug': self.slug})  # 'add_to_card' is url

    def get_remove_from_cart_url(self):
        return reverse('remove_from_cart',
                       kwargs={'slug': self.slug})

    def get_delete_from_cart_url(self):
        return reverse('delete_from_cart',
                       kwargs={'slug': self.slug})


class MainOrderItem(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    complete = models.BooleanField(default=False, null=True, blank=False)
    product = models.ForeignKey(Item, on_delete=models.SET_NULL, blank=True,
                                null=True)
    order = models.ForeignKey('MainOrder', on_delete=models.SET_NULL,
                              blank=True,
                              null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Zamówione artykuły'

    # def get_order(self):
    #     return self.order.mainorder.id

    def get_price(self):
        return self.product.price

    def get_total_item_price(self):
        total = self.product.price * self.quantity
        return round(total, 2)

    def get_total_item_discount_price(self):
        total = self.product.discount_price * self.quantity
        return round(total, 2)

    def get_amount_saved(self):
        return '%.2f' % (round(
            self.get_total_item_price() - self.get_total_item_discount_price(),
            2))

    def get_final_price(self):
        if self.product.discount_price:
            return self.get_total_item_discount_price()
        return self.get_total_item_price()

    def get_final_quantity(self):
        return self.quantity

    def __str__(self):
        return f'{self.quantity} of {self.product}'


class Shipment(models.Model):
    key = models.CharField(
        max_length=50,
        null=True,
        verbose_name='Identyfikator'
    )
    company = models.CharField(
        max_length=50,
        null=True,
        verbose_name='Dostawca'
    )
    price = models.FloatField(
        default=0,
        verbose_name='Cena'
    )
    date_start = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Czas dostawy'
    )

    def __repr__(self):
        return str(self.id)


class ShippingData(models.Model):
    name = models.CharField(max_length=100, null=True)
    second_name = models.CharField(max_length=100, null=True)
    company = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=200, null=True)
    street = models.CharField(max_length=200, null=True)
    zipcode = models.CharField(max_length=200, null=True)
    phone = models.CharField(max_length=11, null=True)
    shipment = models.CharField(max_length=200, null=True)
    payment_options = models.CharField(max_length=200, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shipment


class MainOrder(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    customer = models.ManyToManyField(Customer, verbose_name='Klient')
    date_ordered = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Czas zamówienia'
    )
    complete = models.BooleanField(
        default=False,
        null=True,
        blank=False,
        verbose_name='Kompletny'
    )
    is_shipped = models.BooleanField(
        default=False,
        verbose_name='Wysłane',
    )
    is_shipped_time = models.DateTimeField(
        auto_now_add=True,
        null=True
    )
    items = models.ManyToManyField(
        MainOrderItem,
        verbose_name='Zamówione artykuły',
    )
    shipping_data = models.ForeignKey(
        ShippingData,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Wysyłka',
    )
    canceled = models.BooleanField(
        default=False,
        verbose_name='Anulowane',
    )
    canceled_time = models.DateTimeField(
        auto_now_add=True,
        null=True
    )

    class Meta:
        verbose_name = 'Zamówienia'

    def __str__(self):
        return str(self.id)

    def get_cart_total(self):
        orderitems = self.mainorderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return "%.2f" % (round(total, 2))

    def get_cart_items(self):
        return sum([item.get_final_quantity() for item in self.items.all()])

    def get_total(self):
        total = 0
        for item in self.items.all():
            total += item.get_final_price()
        # return "%.2f" % (round(total, 2))
        return round(total, 2)

    def get_absolute_url(self):
        return reverse('order_view',
                       kwargs={'slug': str(self.id)})

    def get_absolute_url_admin(self):
        return reverse('admin_order_view',
                       kwargs={'slug': str(self.id)})

    def get_absolute_url_user_info(self):
        return reverse('user_info',
                       kwargs={'slug': str(self.user.id)})

    def cancel_order(self):
        return reverse(
            'cancel_order',
            kwargs={'slug': str(self.id)}
        )


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE),
    product = models.ForeignKey(Item, on_delete=models.CASCADE),
    quantity = models.IntegerField(null=False, blank=False),
    created_at = models.DateTimeField(auto_now_add=True)


class Payments(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Użytkownik',
        null=True
    )
    order = models.ForeignKey(
        MainOrder,
        on_delete=models.PROTECT,
        verbose_name='Zamówienia',
    )
    amount = models.FloatField(
        null=True,
        default=0,
        verbose_name='Kwota'
    )
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Czas'
    )

    class Meta:
        verbose_name = 'Płatności'

    def __str__(self):
        return str(self.id)


class Carousel(models.Model):
    photo = models.ImageField(upload_to='photo/%Y/%m/%d/',
                              verbose_name='Zdjęcie', blank=True)
    title = models.CharField(max_length=100, verbose_name='Nazwa')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
