from django.forms import ModelForm

from adminbackend.models import AirtimeDiscount, BillServicesDiscount, VuvuStory
from payments.models import PartnerBank
from users.models import Notifications

class AirtimeDiscountForm(ModelForm):
    class Meta:
        model = AirtimeDiscount
        fields = '__all__'

class NotificationForm(ModelForm):
    class Meta:
        model = Notifications
        fields = ['title','body']

class VuvuStoryForm(ModelForm):
    class Meta:
        model = VuvuStory
        fields = ['youtube_id','description']

class BankChargesForm(ModelForm):
    class Meta:
        model = PartnerBank
        fields = ['deposit_charges']

class BillDiscountForm(ModelForm):
    class Meta:
        model = BillServicesDiscount
        fields = ['rate']