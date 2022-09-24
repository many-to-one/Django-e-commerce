from datetime import datetime
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from .forms import *
import stripe
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import *
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.http import HttpResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import *
from .models import *


def register_page(request):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user) # auth method
            messages.success(request,
                             f"Witamy {user}, teraz jesteś zarejestrowany")
            return redirect("home")
        messages.error(request,
                       "Rejestracja się nie powiodła")

    context = {'form': form}
    return render(request, 'core/register_page.html', context)


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user is not None:
            login(request, user)
            messages.success(request,
                             f"Witamy {user}, jesteś załogowany")
            return redirect('home')
        else:
            messages.error(request, 'Nie jesteś zarejestrowany')
            return redirect('register_page')

    return render(request, 'core/login.html')


def logout_page(request):
    order, created = MainOrder.objects.get_or_create(user=request.user,
                                        complete=False)
    for item in order.items.all():
        inventory = item.product.quantity + item.quantity
        Item.objects.filter(slug=item.product.slug).update(
            quantity=inventory
        )
        item.delete()
    order.delete()
    logout(request)
    messages.success(request, 'Wyłogowano')
    return redirect('login_page')


class PasswordChange(PasswordChangeView):
    form = PasswordChangingForm
    template_name = 'core/password_change.html'
    success_url = reverse_lazy('login_page')


def category_home_view(request):
    categories = Category.objects.all()
    carousel = Carousel.objects.all()
    context = {
        'categories': categories,
        'carousel': carousel,
    }
    return render(request, 'core/category_home_view.html', context)


class AllProductsView(DetailView):
    model = Item
    template_name = 'core/item_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Item.objects.filter(is_published=True)


class ProductsByCategory(ListView):
    template_name = 'core/item_list.html'
    context_object_name = 'products'
    allow_empty = False  # 404 for Client if none

    def get_queryset(self):
        return Item.objects.filter(category__slug=self.kwargs['slug'],
                                   is_published=True)


class ProductView(DetailView):
    model = Item
    context_object_name = 'product'
    template_name = 'core/product_view.html'

    def get_queryset(self):
        return Item.objects.all()


class CategoryView(ListView):
    model = Category
    template_name = 'core/header.html'
    context_object_name = 'category'

    def get_queryset(self):
        return Category.objects.all()


def check_out(request):
    if request.user.is_authenticated:
        user = request.user
        order, created = MainOrder.objects.get_or_create(user=user,
                                                         complete=False)
        items = order.mainorderitem_set.all()
    else:
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        items = []
    context = {'items': items, 'order': order}

    return render(request, 'core/check_out.html', context)


class CheckOutView(View):
    def get(self, *args, **kwargs):
        form = CheckOutForm()
        order, created = MainOrder.objects.get_or_create(
            user=self.request.user,
            complete=False,
        )
        context = {'form': form, 'order': order}
        return render(self.request, 'core/check_out.html', context)

    def post(self, *args, **kwargs):
        form = CheckOutForm(self.request.POST or None)
        try:
            order = MainOrder.objects.get(
                user=self.request.user,
                complete=False,
            )
            if form.is_valid():
                name = form.cleaned_data.get('name')
                second_name = form.cleaned_data.get('second_name')
                company = form.cleaned_data.get('company')
                street = form.cleaned_data.get('street')
                city = form.cleaned_data.get('city')
                zipcode = form.cleaned_data.get('zipcode')
                phone = form.cleaned_data.get('phone')
                shipment = form.cleaned_data.get('shipment')
                save_info = form.cleaned_data.get('save_info')
                payment_options = form.cleaned_data.get('payment_options')
                shipping_data = ShippingData(
                    name=name,
                    second_name=second_name,
                    company=company,
                    street=street,
                    city=city,
                    zipcode=zipcode,
                    phone=phone,
                    shipment=shipment,
                    payment_options=payment_options,
                )
                shipping_data.save()
                order.shipping_data = shipping_data
                order.save()
                print(form.cleaned_data)
                print('The form is valid')
                messages.success(self.request,
                                 'Twoje dane zostały zatwierdzone')
                return redirect('payment_card')
            print(self.request.POST)
            messages.warning(self.request, 'Forma zawiera błędy')
            return redirect("check_out")
        except ObjectDoesNotExist:
            messages.error(self.request, 'Nie złożyłeś zamówienia')
            return redirect('check_out')


def payment_card(request):
    if request.user.is_authenticated:
        user = request.user
        order, created = MainOrder.objects.get_or_create(
            user=user,
            complete=False,
        )
    else:
        order = {'get_cart_total': 0, 'get_cart_items': 0}
    context = {'order': order}

    return render(request, 'core/payment_card.html', context)


@login_required
def add_to_cart(request, slug):  # 33 minuta rolika
    if request.user.is_authenticated:
        product = get_object_or_404(Item, slug=slug)
        order_item, created = MainOrderItem.objects.get_or_create(
            product=product,
            user=request.user,
            complete=False,
        )
        order_qs = MainOrder.objects.filter(user=request.user,
                                            complete=False)
        if order_qs.exists() and product.quantity > 0:
            order = order_qs[0]
            # Check if the order item is in the order
            if order.items.filter(product__slug=product.slug).exists():
                order_item.quantity += 1
                order_item.save()
                inventory = order_item.product.quantity - 1
                Item.objects.filter(slug=slug).update(
                    quantity=inventory
                )
                messages.info(request,
                              "Artykół został dodany do koszyka ponownie")
                # print(connection.query)
                return redirect("cart")
            else:
                if product.quantity > 0:
                    messages.info(request, "Artykół został dodany do koszyka")
                    order.items.add(order_item)
                    order_item.quantity += 1
                    order_item.save()
                    inventory = order_item.product.quantity - 1
                    Item.objects.filter(slug=slug).update(
                        quantity=inventory
                    )
                    # print(connection.query)
                    return redirect("product", slug=slug)
                else:
                    messages.info(request, "Aktualnie artykułu nie ma na stanie")
        else:
            date_ordered = timezone.now()
            order = MainOrder.objects.create(user=request.user,
                                             date_ordered=date_ordered)
            order_item, created = MainOrderItem.objects.get_or_create(
                product=product,
                user=request.user,
                complete=False,
            )
            if product.quantity > 0:
                order.items.add(order_item)
                order_item.quantity += 1
                order_item.save()
                inventory = order_item.product.quantity - 1
                Item.objects.filter(slug=slug).update(
                    quantity=inventory
                )
                messages.info(request, "Artykół został dodany do koszyka")
                return redirect("product", slug=slug)
            else:
                messages.info(request, "Aktualnie artykułu nie ma na stanie")
                return redirect("product", slug=slug)
    else:
        messages.info(request, "Załoguj się")
        return redirect("/")


@login_required
def remove_from_cart(request, slug):
    product = get_object_or_404(Item, slug=slug)
    order_qs = MainOrder.objects.filter(
        user=request.user,
        complete=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # Check if the order item is in the order
        if order.items.filter(product__slug=product.slug).exists():
            removing_item = MainOrderItem.objects.get(
                user=request.user,
                product=product,
                complete=False,
            )
            removing_item.quantity -= 1
            removing_item.save()
            inventory = removing_item.product.quantity + 1
            Item.objects.filter(slug=slug).update(
                quantity=inventory
            )
            messages.info(request, "Artykół został usunięty z koszyka")
            if removing_item.quantity == 0:
                removing_item.delete()
                messages.info(request, "Tego artykółu nie ma juz w koszyku")
            return redirect('cart')
        else:
            messages.info(request, "Tego artykółu nie ma w koszyku")
            return redirect('cart')
    else:
        messages.info(request, "Nie złożyłeś jeszcze żadnego zamówienia")
        return redirect('cart')

def delete_from_cart(request, slug):
    product = get_object_or_404(Item, slug=slug)
    order = MainOrder.objects.filter(
        user=request.user,
        complete=False
    )
    removing_item = MainOrderItem.objects.get(
        user=request.user,
        product=product,
        complete=False,
    )
    removing_item.delete()
    inventory = removing_item.product.quantity + removing_item.quantity
    Item.objects.filter(slug=slug).update(
        quantity=inventory
    )
    messages.info(request, "Artykół został usunięty")
    return redirect("cart")


@login_required
def cart(request):
    if request.user.is_authenticated:
        customer = request.user
        order, created = MainOrder.objects.get_or_create(user=customer,
                                                         complete=False)
    else:
        order = {'get_cart_total': 0, 'get_cart_items': 0}
    context = {'order': order}
    return render(request, 'core/cart3.html', context)


stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(generic.View):
    def post(self, *args, **kwargs):
        host = self.request.get_host()
        order_id = self.request.POST.get('order_id')
        order = MainOrder.objects.get(id=order_id)
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'blik'],
                line_items=[
                    {
                        # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                        'price_data': {
                            'currency': 'pln',
                            'unit_amount': int(order.get_total()*100),
                            'product_data': {
                                'name': order.id,
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=f"http://{host}{reverse('payment_success')}",
                cancel_url=f"http://{host}{reverse('payment_cancel')}",
            )

            if checkout_session:
                # payments = Payments()
                # payments.user = self.request.user
                # payments.order = order
                # # payments.order_items = order_items
                # payments.amount = int(order.get_total())
                # payments.date = datetime.now().time()
                # payments.save()

                MainOrder.objects.filter(complete=False).update(
                    complete=True)
                MainOrderItem.objects.filter(complete=False).update(
                    complete=True)

        except Exception as e:
            for item in order.items.all():
                new_inventory = item.product.quantity + item.quantity
                Item.objects.filter(title=item.product.title).update(
                    quantity=new_inventory
                )
            MainOrder.objects.filter(complete=False).update(
                complete=False)
            MainOrderItem.objects.filter(complete=False).update(
                complete=False)
            return str(e)
        # if checkout_session:

        return redirect(checkout_session.url, code=303)


def payment_success(request):
    return render(request, 'core/payment_success.html')


def paymentCancel(request):
    context = {
        'payment_status': 'cancel'
    }
    return render(request, 'core/check_out.html', context)


@csrf_exempt
def my_webhook_view(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Passed signature verification
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        if session.payment_status == 'paid':
            line_item = session.list_line_items(session.id, limit=1).data[0]
            order_id = line_item['description']
    return HttpResponse(status=200)


def my_orders(request):
    orders = MainOrder.objects.filter(user=request.user).order_by('-id')
    context = {'orders': orders}
    return render(request, 'core/my_orders.html', context)


def order_view(request, slug):
    order = MainOrder.objects.get(id=slug, user=request.user, )
    # payments = order.payments_set.all()
    context = {'order': order}
    return render(request, 'core/order_view.html', context)

def cancel_order(request, slug):
    orders = MainOrder.objects.all()
    order = MainOrder.objects.get(id=slug, user=request.user)
    context = {'order': order, 'orders': orders}
    if order.is_shipped == False:
        order.canceled = True
        order.canceled_time = datetime.now()
        order.save()
        messages.warning(request, 'Twoje zamówienie zostało anulowane')
        return render(request, 'ecommerce/cancel_orders.html', context)
    else:
        messages.info(request, 'Zamówienia zostało już wysłane!')
        return render(request, 'core/my_orders.html')


def cancel_orders(request):
    orders = MainOrder.objects.filter(canceled=True)
    context = {'orders': orders}
    return render(request, 'core/cancel_orders.html', context)


@staff_member_required
def all_orders(request):
    orders = MainOrder.objects.all().order_by('-id')
    if request.method == 'POST':
        check = request.POST.getlist('checks[]')
        for val in check:
            order = MainOrder.objects.get(pk=val)
            order.is_shipped = True
            order.is_shipped_time = datetime.now()
            order.save()
    context = {
        'orders': orders,
    }
    return render(request, 'core/all_orders.html', context)


def shipped_orders(request):
    shipped_or = MainOrder.objects.filter(is_shipped=True).order_by('-id')
    context = {
        'shipped_or': shipped_or,
    }
    return render(request, 'core/shipped_orders.html', context)


def unshipped_orders(request):
    unshipped_or = MainOrder.objects.filter(is_shipped=False).order_by('-id')
    if request.method == 'POST':
        check = request.POST.getlist('checks[]')
        for val in check:
            order = MainOrder.objects.get(pk=val)
            order.is_shipped = True
            order.is_shipped_time = datetime.now()
            order.save()
    context = {
        'unshipped_or': unshipped_or,
    }
    return render(request, 'core/unshipped_orders.html', context)


@staff_member_required
def admin_order_view(request, slug):
    order = MainOrder.objects.get(id=slug)
    context = {'order': order}
    return render(request, 'core/admin_order_view.html', context)


@staff_member_required
def customer_view(request, slug):
    customer = Customer.objects.filter(id=slug, user=request.user)
    context = {'customer': customer}
    return render(request, 'core/customer.html', context)


def user_info(request, slug):
    user = User.objects.get(id=slug)
    orders = MainOrder.objects.filter(user=user)
    context = {'user': user, 'orders': orders, }
    return render(request, 'core/user_info.html', context)



