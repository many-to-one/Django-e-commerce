from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import *


class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1',
                  'password2']


class PasswordChangingForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'type': 'password'}
        )
    )
    new_password1 = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'type': 'password'}
        )
    )
    new_password2 = forms.CharField(
        max_length=100,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'type': 'password'}
        )
    )

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')


PAYMENT_CHOICES = (
    # ('Credit Card', 'Credit Card'),
    # ('PayPal', 'PayPal'),
    ('Płatność przy odbiorze', 'Płatność przy odbiorze'),
    ('Przelew na konto firmowe', 'Przelew na konto firmowe')
)


SHIPMENT_CHOICES = (
    ('InPost(paczkomat)', 'InPost(paczkomat)'),
    ('InPost(za pobraniem)', 'InPost(za pobraniem)'),
    ('DPD(za pobraniem)', 'DPD(za pobraniem)'),
)


class CheckOutForm(forms.Form):
    name = forms.CharField(max_length=100)
    second_name = forms.CharField(max_length=100)
    company = forms.CharField(max_length=100)
    zip = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': '12-345', 'class': 'mb-3'})
    )
    street = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'ul. Przykładowa 1a'})
    )
    city = forms.CharField(max_length=100)
    phone = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={'placeholder': '123-456-789'})
    )
    shipment = forms.ChoiceField(
        # queryset=Shipment.objects.all(),
        choices=SHIPMENT_CHOICES
    )
    save_info = forms.BooleanField(
        widget=forms.CheckboxInput(),
        required=False
    )
    payment_options = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=PAYMENT_CHOICES,
    )


