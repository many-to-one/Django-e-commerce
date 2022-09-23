from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import *
from django import forms

# from .views import CreateCheckoutSessionView


class ItemAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = Item
        fields = '__all__'


class CategoryAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = Category
        fields = '__all__'



class MainOrderAdminForm(forms.ModelForm):

    class Meta:
        model = MainOrder
        fields = '__all__'


class MainOrderItemAdminForm(forms.ModelForm):

    class Meta:
        model = MainOrderItem
        fields = '__all__'


class ShipmentAdminForm(forms.ModelForm):

    class Meta:
        model = Shipment
        fields = '__all__'


class ShippingDataAdminForm(forms.ModelForm):

    class Meta:
        model = ShippingData
        fields = '__all__'


# class PaymentsAdminForm(forms.ModelForm):
#     class Meta:
#         model = Payments
#         fields = '__all__'


class MainOrderAdmin(admin.ModelAdmin):
    form = MainOrderAdminForm
    list_display = (
       'id', 'user', 'date_ordered', 'complete',
    )
    list_display_links = (
        'id', 'user'
    )


class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'product',
        'quantity',
        'created_at',
    )


class MainOrderItemAdmin(admin.ModelAdmin):
    # prepopulated_fields = {"slug": ("title",)}
    form = MainOrderItemAdminForm
    list_display = (
        'id', 'user', 'get_photo', 'product', 'get_final_quantity',
        'get_price',
        'get_discount_price',
        'get_final_price',
        # 'quantity',
        # 'get_order',
    )
    list_display_links = ('id', 'user', )

    def get_photo(self, obj):
        if obj.product.photo:
            return mark_safe(f'<img src="{obj.product.photo.url}" width="50">')
        else:
            return '-'

    def get_discount_price(self, obj):
        if obj.product.discount_price:
            return obj.product.discount_price
        else:
            return '-'


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    form = CategoryAdminForm
    list_display = (
        'id', 'get_photo', 'title',
    )
    list_display_links = ('id', 'title')

    def get_photo(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="50">')
        else:
            return '-'

    get_photo.short_description = 'Zdjęcie'


class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    form = ItemAdminForm
    list_display = (
        'id', 'get_photo', 'title', 'price', 'discount_price', 'category',
        'created_at', 'views', 'quantity',
        'updated_at',
        'slug',
    )
    list_display_links = ('id', 'title')
    search_fields = ('title',)
    list_filter = ('category',)
    readonly_fields = ('views', 'created_at', 'updated_at', 'get_photo')
    fields = (
        'title', 'short_title', 'slug', 'category', 'price', 'discount_price',
        'quantity', 'content', 'photo', 'get_photo', 'views', 'created_at',
    )
    save_on_top = True  # knopka dla sochranenija w werchu

    # save_as = True #na etapie razrabotki dublirujet sozdanyj object,
    # da i wo wremya zapolnienija sajta kontentom nużnyje polia uże zapolnieny

    def get_photo(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="50">')
        else:
            return '-'

    get_photo.short_description = 'Zdjęcie'


class ShipmentAdmin(admin.ModelAdmin):
    form = ShipmentAdminForm
    list_display = ('id', 'key', 'company', 'price', 'date_start')
    list_display_links = ('id', 'company')


class ShippingsAdmin(admin.ModelAdmin):
    form = ShippingDataAdminForm
    list_display = ('id', 'company', 'name', 'second_name', 'city')
    list_display_links = ('id', 'company')


# class PaymentsAdmin(admin.ModelAdmin):
#     form = PaymentsAdminForm
#     list_display = ('id', 'user', 'amount', 'date',)
#     list_display_links = ('user',)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(MainOrder, MainOrderAdmin)
admin.site.register(MainOrderItem, MainOrderItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Shipment, ShipmentAdmin)
admin.site.register(ShippingData, ShippingsAdmin)
# admin.site.register(Payments, PaymentsAdmin)

