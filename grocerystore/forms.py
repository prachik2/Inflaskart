#-*- coding: UTF-8 -*-
import re
from datetime import date
from calendar import monthrange
from django import forms
from django.contrib.auth.models import User
from .models import Product, ProductCategory, ProductSubCategory, Dietary, \
                    Store, Address, Availability, Inflauser, State, Zipcode

"""
This module contains 5 forms:

- UserForm: 1st part of the user registration template;
- AddressForm: 2nd part of the user registration template;
- LoginForm
- SelectCategory: used to select a product top category
- PaymentForm (whose 'number' field uses the CreditCardField class)

"""

class UserForm(forms.ModelForm):
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']
        help_texts = {
            'username': None,
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class AddressForm(forms.ModelForm):
    zip_code = forms.RegexField(max_length=5, min_length=4, regex=r'^[0-9]{4,5}$',
               error_messages={'invalid': "Please enter a valid ZIP code",
                               'required': "Please fill in this field."})

    class Meta:
        model = Address
        fields = '__all__'


class LoginForm(forms.ModelForm):
    password = forms.CharField(max_length=50, min_length=8, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password']
        help_texts = {
            'username': None,
        }


class SelectCategory(forms.Form):
    """Displays a drop down menu with all the product categories available
    in a given store"""
    category = forms.ModelChoiceField(label='Choose a category',
                                      queryset=ProductCategory.objects.all(),
                                      empty_label="--Choose below--",
                                      widget=forms.Select(attrs={'onChange':'submit();'}))


class CreditCardField(forms.IntegerField):
    """Copied from http://codekarate.com/blog/django-credit-card-payment-form"""
    def get_cc_type(self, number):
        """
        Gets credit card type given number. Based on values from Wikipedia page
        "Credit card number"
        """
        number = str(number)
        if len(number) == 13:
            if number[0] == "4":
                return "Visa"
        elif len(number) == 14:
            if number[:2] == "36":
                return "MasterCard"
        elif len(number) == 15:
            if number[:2] in ("34", "37"):
                return "American Express"
        elif len(number) == 16:
            if number[:4] == "6011":
                return "Discover"
            if number[:2] in ("51", "52", "53", "54", "55"):
                return "MasterCard"
            if number[0] == "4":
                return "Visa"
        return "Unknown"

    def clean(self, value):
        """Check if given CC number is valid and one of the accepted card types
        by overriding the django.forms.IntegerField.clean() method."""
        if value and (len(value) < 13 or len(value) > 16):
            raise forms.ValidationError("Please enter in a valid credit card number.")
        elif self.get_cc_type(value) not in ("Visa", "MasterCard", "American Express", "Discover"):
            raise forms.ValidationError("Please note that we only accept Visa, "\
                  "MasterCard, Discover, and American Express credit cards.")
        return super(CreditCardField, self).clean(value)


class PaymentForm(forms.Form):
    number = CreditCardField(label="Card Number")
    first_name = forms.CharField(label="Card Holder First Name", max_length=30)
    last_name = forms.CharField(label="Card Holder Last Name", max_length=30)
    expire_month = forms.ChoiceField(choices=[(x, x) for x in range(1, 13)])
    expire_year = forms.ChoiceField(choices=[(x, x) for x in range(date.today().year, date.today().year + 15)])
    cvv_number = forms.IntegerField(label="CVV Number", max_value= 9999,
                                    widget=forms.TextInput(attrs={'size': '4'}))

    def __init__(self, *args, **kwargs):
        self.payment_data = kwargs.pop('payment_data', None)
        super(PaymentForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(PaymentForm, self).clean()
        expire_month = cleaned_data.get('expire_month')
        expire_year = cleaned_data.get('expire_year')

        if expire_year in forms.fields.EMPTY_VALUES:
            self._errors["expire_year"] = self.error_class(["You must select a valid Expiration year."])
            del cleaned_data["expire_year"]
        if expire_month in forms.fields.EMPTY_VALUES:
            self._errors["expire_month"] = self.error_class(["You must select a valid Expiration month."])
            del cleaned_data["expire_month"]

        year = int(expire_year)
        month = int(expire_month)
        # find last day of the month
        day = monthrange(year, month)[1]
        expire = date(year, month, day)

        if date.today() > expire:
            self._errors["expire_year"] = self.error_class(["The expiration date you entered is in the past."])

        return cleaned_data
