from django.contrib.auth.forms import UserCreationForm,SetPasswordForm
from django.contrib.auth import password_validation
from django.forms import forms

from users.models import User


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