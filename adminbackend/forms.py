from django.forms import ModelForm

from adminbackend.models import AirtimeDiscount

class AirtimeDiscountForm(ModelForm):
    class Meta:
        model = AirtimeDiscount
        fields = '__all__'