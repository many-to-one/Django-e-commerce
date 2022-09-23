from django import template
from core.models import *

register = template.Library()


@register.simple_tag
def get_cart_items(user):
    order, created = MainOrder.objects.get_or_create(user=user,
                                                     complete=False)
    return order.get_cart_items()
