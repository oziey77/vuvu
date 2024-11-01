from django.contrib.auth.forms import UserCreationForm,SetPasswordForm
from django.contrib.auth import password_validation
from django import forms

from users.models import KYCData, Story, User


class MyUserCreationForm(UserCreationForm):
    password2 = None
    def clean_email(self):
        email = self.cleaned_data['email']
        return email.lower()

    def clean_username(self):
        username = self.cleaned_data['username']
        return username.lower()
    class Meta:
        model = User
        fields =['phone_number','username','password1','email','referral_code']

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        try:
            password_validation.validate_password(password1, self.instance)
        except forms.ValidationError as error:

            # Method inherited from BaseForm
            self.add_error('password1', error)
        return password1
    
class KYCDataForm(forms.ModelForm):
    class Meta:
        model = KYCData
        fields = "__all__"
        exclude = ["user","status","dob"]

class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ["body"]

# Multiple File upload
# class MultipleFileInput(forms.ClearableFileInput):
#     allow_multiple_selected = True


# class MultipleFileField(forms.FileField):
#     def __init__(self, *args, **kwargs):
#         kwargs.setdefault("widget", MultipleFileInput())
#         super().__init__(*args, **kwargs)

#     def clean(self, data, initial=None):
#         single_file_clean = super().clean
#         if isinstance(data, (list, tuple)):
#             result = [single_file_clean(d, initial) for d in data]
#         else:
#             result = [single_file_clean(data, initial)]
#         return result


# class FileFieldForm(forms.Form):
#     file_field = MultipleFileField()

