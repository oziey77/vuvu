from django.forms import ModelForm

from adminbackend.models import AirtimeDiscount, VuvuStory
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