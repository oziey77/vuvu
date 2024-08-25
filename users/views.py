import json
import random
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout ,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator,PasswordResetTokenGenerator
from django.utils.encoding import force_bytes,force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError

from users.forms import MyUserCreationForm
from vuvu.custom_functions import is_ajax, reference
from .models import User, UserConfirmation, UserWallet

import uuid
import random
import string
from django.contrib.auth.hashers import make_password,check_password

from django.utils import  six
from django.contrib.sites.shortcuts import get_current_site

# Account Activation Token
class TokenGenerator(PasswordResetTokenGenerator):  
    def _make_hash_value(self, user, timestamp):  
        return (  
            six.text_type(user.pk) + six.text_type(timestamp) +  
            six.text_type(user.email_verified)  
        )  
account_activation_token = TokenGenerator()


# Register page
def signupPage(request):
    if is_ajax(request=request) and request.method == "POST":
        print(request.POST)
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  
            UserWallet.objects.create(
                user = user,
            )          
            refCode = reference(6)
            try:
                existing = User.objects.get(referral_code=refCode)
                while existing is not None:
                    refCode = reference(6)
                    existing = User.objects.get(referral_code=refCode)
            except ObjectDoesNotExist:
                # Set user referral  codes and create wallet
                user.is_active = False
                user.referral_code = refCode
                user.save()   

            OTPCode = random.randrange(111111, 999999, 5)    
            confirmationID = reference(16)
            confirmationData = UserConfirmation.objects.create(
                user = user,
                confirmation_id = confirmationID.lower(),
                otp = OTPCode,
                
            )  
            confirmationData.refresh_from_db()         

            # Send activation Email
            current_site = get_current_site(request)  
            mail_subject = 'Please confirm your email address'  
            message = render_to_string('users/email/acc_active_email.html', {  
                'user': user,  
                'domain': current_site.domain,  
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),  
                'token':account_activation_token.make_token(user),  
            })  
            # to_email = form.cleaned_data.get('email') 
            send_mail(mail_subject, message, "Confirm Email <support@yagapay.io>", [user.email])
            return JsonResponse({
                'code':'00',
                'confirmationID':confirmationData.confirmation_id
            })
        else:
            print(form.errors)
            formErrors = form.errors.as_json()
            data = json.loads(formErrors)
            registrationError = []
            if 'username' in data:    
                errorList = data['username'][0]
                registrationError.append({
                    'usernameError':errorList['message'],
                }) 
            if 'email' in data:    
                errorList = data['email'][0]
                registrationError.append({
                    'emailError':errorList['message'],
                }) 
            if 'phone_number' in data:    
                errorList = data['phone_number'][0]
                registrationError.append({
                    'phoneError':errorList['message'],
                }) 
            if 'password1' in data:    
                errorList = data['password1'][0]
                registrationError.append({
                    'passwordError':errorList['message'],
                })           
            return JsonResponse({
                'code':'09',
                'registrationError':registrationError,
            })
    return render(request,'users/signup.html')

# Confirmation Email Sent page
def confirmEmailSent(request,confirmationID):
    return render(request,'users/confirmation-sent.html')

def activate(request, uidb64, token):  
    # User = get_user_model()  
    try:  
        uid = force_str(urlsafe_base64_decode(uidb64))  
        user = User.objects.get(pk=uid)  
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):  
        user = None  
    if user is not None and account_activation_token.check_token(user, token):  
        user.is_active = True  
        user.save()
        # messages.success(request,'Acccount activated. You can login your account.')
        return render(request,'users/email-confirmed.html') 
    else:  
        messages.error(request,'Invalid activation link.')
        return redirect('login')
    
# Password Reset Successful page
def passwordResetSuccessfulPage(request):
    return render(request,'users/password-reset-successful.html')

# Login page
def loginPage(request):
    user = request.user
    if user.is_authenticated:
        if user.is_staff:
            return redirect('overview')
        else:                        
            return redirect('dashboard')
    else:
        if request.method == 'POST':
            email = request.POST['email'].lower().strip()
            password = request.POST['password']
            # remember = request.POST.get('remember',None)


            try:
                user = User.objects.get(email=email)
                loginAttemptLeft = user.login_attempts_left

                if loginAttemptLeft > 0:                
                    user.login_attempts_left -= 1
                    user.save()
                    user = authenticate(request,email=email,password=password)               
                
                    if user is not None:
                        user.login_attempts_left = 3
                        user.save()

                        login(request,user)
                        # loginMessage.delay(username=user.username)
                        # if remember == None:
                        #     request.session.set_expiry(0)

                        if user.is_staff:
                            return redirect('overview')
                        else:                                               
                            return redirect('dashboard')
                    
                    else: 
                        # messages.error(request,'Login input is incorrect 1')
                        messages.error(request, f"{loginAttemptLeft} Login attempts remaining")
                else:
                    pass
                    # return redirect("otp")

            except ObjectDoesNotExist:
                messages.error(request,'email/password not correct')
    return render(request,'users/login.html')

# Forgot Password page
def forgotPasswordPage(request):
    return render(request,'users/forgot-password.html')

# Password Reset Sent page
def passwordResetSentPage(request):
    return render(request,'users/password-reset-sent.html')

# Password Reset Successful page
def passwordResetSuccessfulPage(request):
    return render(request,'users/password-reset-successful.html')

# Password Reset Successful page
@login_required(login_url='login')
def dashboardPage(request):
    user = request.user

    print(f"USER firstname is {user.first_name}")
    context = {

    }
    return render(request,'users/dashboard.html',context)

@login_required(login_url='login')
def fetchWalletBalance(request):
    if is_ajax(request) and request.method == "GET":
        walletInfo = request.user.wallet_balances
        return JsonResponse({
            'code':'00',
            'balance': walletInfo['balance'],
            'cashback': walletInfo['cashback'],
            'referral_bonus': walletInfo['referral_bonus'],
        })

