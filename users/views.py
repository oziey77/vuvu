from datetime import datetime,timedelta
from decimal import Decimal
import json
import random
from django.http import JsonResponse
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout ,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator,PasswordResetTokenGenerator
from django.utils.encoding import force_bytes,force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail, BadHeaderError
import requests

from adminbackend.models import DataBackend, VuvuStory
from payments.models import DynamicAccountBackend, OneTimeDeposit, PartnerBank, WalletFunding
from telecomms.models import ATNDataPlans, DataServices
from telecomms.serializers import ATNDataPlanSerializer
from users.forms import KYCDataForm, MyUserCreationForm, StoryForm
from users.serializers import TransactionSerializer
from users.tasks import sendConfirmOTP, sendPasswordOTP
from vuvu.custom_functions import GIVEAWAY_DATA, is_ajax, isNum, reference,offers
from .models import AccountDeleteQueue, Cashback, KYCData, Notifications, SafeHavenAccount, Transaction, TransactionPIN, User, UserConfirmation, UserWallet, WalletActivity, ZipFileModel

import uuid
import random
import string
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth.forms import PasswordResetForm,PasswordChangeForm,SetPasswordForm

from django.utils import  six
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from django.db.models import Q
import tempfile
import os
import zipfile
from django.core.files import File
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
            sendConfirmOTP.delay(username=user.username,email=user.email,otp=OTPCode) 
            return JsonResponse({
                'code':'00',
                'confirmationID':confirmationData.confirmation_id
            })
        else:
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

def resendRegOTP(request):
    if is_ajax(request) and request.method == "GET":
        confirmationID = request.GET.get('confirmationID')
        try:
            confirmationData = UserConfirmation.objects.get(confirmation_id=confirmationID)
            if confirmationData is not None:
                OTPCode = random.randrange(111111, 999999, 5) 
                confirmationData.otp = OTPCode
                confirmationData.save()
                return JsonResponse({
                    "code":"00",
                    "message":"OTP resent successfully"
                }) 
        except ObjectDoesNotExist:
            return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })


# Confirmation Email Sent page
def confirmEmailSent(request,confirmationID):
    context = {
        "confirmationID":confirmationID,
    }
    return render(request,'users/confirmation-sent.html',context)

def verifyRegistration(request):
    if is_ajax(request) and request.method == "GET":
        confirmationID = request.GET.get('confirmationID')
        OTPCode = request.GET.get('otp')
        try:
            confirmationData = UserConfirmation.objects.get(confirmation_id=confirmationID)
            if confirmationData is not None:
                if confirmationData.otp == OTPCode:
                    user = confirmationData.user
                    user.is_active = True
                    user.save()
                    login(request,user)
                    confirmationData.delete()
                    return JsonResponse({
                        "code":"00",
                        "message":"Registration successful"
                    })
                else:
                   return JsonResponse({
                        "code":"09",
                        "message":"Invalid OTP Code"
                    }) 
        except ObjectDoesNotExist:
            return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })
    else :
        return JsonResponse({
            "code":"09",
            "message":"Invalid request"
        })

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
        elif user.staff == False and user.is_admin:
            return redirect('all-users')
        else:                        
            return redirect('dashboard')
    else:
        if request.method == 'POST':
            username = request.POST['username'].lower().strip()
            password = request.POST['password']
            # remember = request.POST.get('remember',None)


            try:
                user = User.objects.get(username=username)
                loginAttemptLeft = user.login_attempts_left

                if loginAttemptLeft > 0:                
                    user.login_attempts_left -= 1
                    user.save()
                    loginAttemptLeft = user.login_attempts_left
                    user = authenticate(request,username=username,password=password)  
                             
                
                    if user is not None:
                        user.login_attempts_left = 3
                        user.save()

                        login(request,user)
                        # if remember == None:
                        #     request.session.set_expiry(0)

                        if user.is_staff:
                            return redirect('overview')
                        elif user.staff == False and user.is_admin:
                            return redirect('all-users')
                        else:                                               
                            return redirect('dashboard')
                    
                    else: 
                        messages.error(request,'username/password is incorrect')
                        messages.error(request, f"{loginAttemptLeft} Login attempts remaining")
                        return redirect('login')
                else:
                    return redirect("forgot-password")

            except ObjectDoesNotExist:
                messages.error(request,'username/password is incorrect')
                return redirect('login')
    return render(request,'users/login.html')

def logoutUser(request):
    logout(request)
    return redirect('login')
# Forgot Password page
def forgotPasswordPage(request):    
    return render(request,'users/forgot-password.html')

# Forgot Password page
def sendOTP(request):    
    if is_ajax(request) and request.method == "POST":
        email = request.POST.get('email').strip().lower()
        try:
            user = User.objects.get(email=email)
            if user is not None:
                OTPCode = random.randrange(111111, 999999, 5)  
                confirmationID = reference(16)
                confirmationData = ''
                try:
                    oldData = UserConfirmation.objects.get(user = user)
                    if oldData is not None:
                        oldData.confirmation_id =confirmationID
                        oldData.otp = OTPCode
                        oldData.save()
                        confirmationData = oldData
                except ObjectDoesNotExist:
                    confirmationData = UserConfirmation.objects.create(
                        user = user,
                        confirmation_id = confirmationID.lower(),
                        otp = OTPCode,                    
                    )
                    confirmationData.refresh_from_db()
                # IMPLEMENT EMAIL SEND
                sendPasswordOTP.delay(username=user.username,email=user.email,otp=OTPCode) 

                return JsonResponse({
                    "code":"00",
                    "confirmCode":confirmationData.confirmation_id
                })


        except ObjectDoesNotExist:
            return JsonResponse({
                "code":"09",
                "message":"No record found for the email address"

            })
    return render(request,'users/forgot-password.html')

# Reset Password
def resetPassword(request):
    if is_ajax(request) and request.method == "POST":
        confirmationID = request.POST.get('confirmationID')
        otp = request.POST.get('otp')
        
        # Get OTP Data
        try:
            OTPData = UserConfirmation.objects.get(confirmation_id=confirmationID,otp=otp)
            if OTPData is not None:
                user = OTPData.user
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    user = form.save()
                    # messages.success(request, 'Your password was successfully updated!')
                    return JsonResponse({
                        'code':'00'
                    })
                else:            
                    formErrors = form.errors.as_json()
                    data = json.loads(formErrors)
                    errorMessages = {}
                    if 'old_password' in data:    
                        errorList = data['old_password'][0]          
                        errorMessages.update({
                            'old_password':errorList
                        })
                    if 'new_password2' in data:    
                        errorList = data['new_password2'][0]          
                        errorMessages.update({
                            'new_password2':errorList
                        })
                    return JsonResponse({
                        'code':'09',
                        'data':errorMessages,
                    })
        except ObjectDoesNotExist:
            return JsonResponse({
                'code':'09',
                'data':"Invalid OTP",
            })
    else:
        return JsonResponse({
                'code':'09',
                'data':"Invalid request",
            })


# Password Reset Sent page
def passwordResetSentPage(request):
    return render(request,'users/password-reset-sent.html')

# Password Reset Successful page
def passwordResetSuccessfulPage(request):
    return render(request,'users/password-reset-successful.html')

# Save Transaction PIN
@login_required(login_url='login')
def saveTransactionPin(request):
    user = request.user
    if is_ajax(request=request) and request.method == 'POST':
        pin1 = request.POST['pin1']
        pin2 = request.POST['pin2']
        if isNum(pin1) == isNum(pin2):
            try:
                transPin = TransactionPIN.objects.get(user=user)
                if transPin is not None:
                    return JsonResponse({
                        'code':'09',
                        'message':'invalid request'
                    })
            except ObjectDoesNotExist:
                TransactionPIN.objects.create(
                    user = user,
                    transaction_pin = make_password(pin1)
                )
                return JsonResponse({
                    'code':'00',
                    'message':'Transaction pin saved'
                })
        else:
            return JsonResponse({
                'code':'09',
                'message':'Invalid pin sequence'
            })

    else:
        return JsonResponse({
            'code':'09',
            'message':'invalid request'
        })
    

# Check Old PIN
@login_required(login_url='login')
def checkTransactionPin(request):
    user = request.user
    if is_ajax(request=request) and request.method == 'GET':
        oldPin = request.GET['oldPIN']
        transPin = TransactionPIN.objects.get(user=user)
        if check_password(oldPin, transPin.transaction_pin):
            return JsonResponse({
                    'code':'00',
                    'message':'Transaction pin updated'
                })
        else:
            return JsonResponse({
                    'code':'09',
                    'message':'Old PIN is incorrect'
                })

@login_required(login_url='login')
def updateTransactionPin(request):
    user = request.user
    if is_ajax(request=request) and request.method == 'POST':
        oldPin = request.POST['oldPIN']
        pin1 = request.POST['pin1']
        pin2 = request.POST['pin2']
        transPin = TransactionPIN.objects.get(user=user)
        if check_password(oldPin, transPin.transaction_pin):
            if isNum(pin1) == isNum(pin2):
                transPin.transaction_pin = make_password(pin1)
                transPin.save()
                return JsonResponse({
                    'code':'00',
                    'message':'Transaction pin updated'
                })
            else:
                return JsonResponse({
                    'code':'09',
                    'message':'Invalid pin sequence'
                })
        else:
            return JsonResponse({
                'code':'01',
                'message':'incorrect old pin'
                })

    else:
        return JsonResponse({
            'code':'09',
            'message':'invalid request'
        })

# Password Reset Successful page
@login_required(login_url='login')
def dashboardPage(request):
    user = request.user
    page = "dashboard"


    
    period = "Morning"
    hourOfDay= datetime.now().time().hour
    if hourOfDay < 12:
        period = "Morning"
    elif hourOfDay >= 12 and hourOfDay < 17:
        period = "Afternoon"
    elif hourOfDay >= 17:
        period = "Evening"

    
    # Unread Notifications 
    unreadNotifications = Notifications.objects.filter(user=user,status="Unread").count()

    # Get Data transaction for progress
    transYear = datetime.now().date().year
    totalDataTrans = Transaction.objects.filter(user=user,transaction_type="Data",status='Success',created__year=transYear).count()
    giveAwayProgress = 0
    
    

    # Give away progress
    giveAwayLevelComplete = False
    giveAwayLevel = user.give_away_level
    currentGiveAway = GIVEAWAY_DATA[f"level{giveAwayLevel}"]
    if giveAwayLevel == 1:    
        if totalDataTrans < 10:
            giveAwayProgress = 20 + ((totalDataTrans/10) * 100)
        if totalDataTrans >= currentGiveAway["transCount"]:
            giveAwayProgress = 100
            giveAwayLevelComplete = True
    else:    
        if totalDataTrans < currentGiveAway["transCount"]:
            giveAwayProgress = ((totalDataTrans/currentGiveAway["transCount"]) * 100)
        if totalDataTrans >= currentGiveAway["transCount"]:
            giveAwayProgress = 100
            giveAwayLevelComplete = True

    pinSet = False
    try:
        transactionPIN = TransactionPIN.objects.get(user=user)
        if transactionPIN is not None:
            pinSet = True
    except ObjectDoesNotExist:
        pass
    context = {
        "pinSet":pinSet,
        "period":period,
        "giveAwayProgress":giveAwayProgress,
        "page":page,
        "unreadNotifications":unreadNotifications,
        "giveAwayLevelComplete":giveAwayLevelComplete,
        "giveAwayLevel":giveAwayLevel,
    }
    return render(request,'users/dashboard.html',context)

# Password Reset Successful page
@login_required(login_url='login')
def claimGiveAway(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        operator = request.GET.get("selectedOperator")
        recipient = request.GET.get("recipient")

        transYear = datetime.now().date().year
        totalDataTrans = Transaction.objects.filter(user=user,transaction_type="Data",created__year=transYear).count()
        giveAwayLevel = user.give_away_level
        currentGiveAway = GIVEAWAY_DATA[f"level{giveAwayLevel}"]
        canClaim = False

        if giveAwayLevel == 1 and totalDataTrans >= currentGiveAway["transCount"]:
            canClaim = True
        elif giveAwayLevel == 2 and totalDataTrans >= currentGiveAway["transCount"]:
            canClaim = True
        
        if canClaim:
            if operator == "MTN":
                networkID = "1"
            elif operator == "Airtel":
                networkID = "2"
            elif operator == "Glo":
                networkID = "3"
            elif operator == "9Mobile":
                networkID = "4"

            # API CALL FOR DATA REWARD
            transRef = reference(26)
            wallet = UserWallet.objects.get(user=user)  
            # Twins10
            apiToken = settings.TWINS10_TOKEN
            url = 'https://twins10.com/api/data'
            payload = {
                        "network": networkID,
                        "phone":recipient,
                        "data_plan":currentGiveAway[operator],
                        "bypass":False,
                        "request-id":transRef                  
                    }
            headers = {
                        'Authorization': f"Token {apiToken}",
                        'Accept': 'application/json'
                    }
            

            response = requests.request('POST', url, headers=headers, json=payload)
            data = response.json()

            
            if data['status'] == "success" or data['status'] == "processing":
                user.give_away_level = 2
                user.save()
                Transaction.objects.create(
                    user = user,
                    operator = operator,
                    transaction_type = "Data",
                    recipient = recipient,
                    reference = transRef,
                    package = currentGiveAway["reward"],
                    message = "Give-away Reward",
                    amount = 0,
                    balanceBefore = wallet.balance,
                    balanceAfter = wallet.balance,
                )
                return JsonResponse({
                    "code":"00"
                })
            elif data['status'] == "fail":
                if 'response' in data:
                    APIResponse = data["response"]
                elif 'message' in data:
                    APIResponse = data["message"]

                if "Insufficient Account" in APIResponse:
                    return JsonResponse({
                    "code":"09",
                    "message":"network downtime!"
                    })
                else:
                    return JsonResponse({
                        "code":"09",
                        "message":APIResponse
                    })
        else:
            return JsonResponse({
                "code":"09",
                "message":"invalid request"
            })

        
    pass

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
    
# Transaction History
@login_required(login_url='login')
def transactionHistoryPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    userTransactions = Transaction.objects.filter(user=user).order_by("-id")

    transaction = ''
    if request.GET.get('transaction'):
        transaction = request.GET.get('transaction')
        if transaction == 'All':
            return redirect('transaction-history')
        else:
            userTransactions = userTransactions.filter(transaction_type=transaction)


    p = Paginator(userTransactions,10)
    page_number = request.GET.get('page')
    try:
        transactions = p.get_page(page_number)
    except PageNotAnInteger:
        transactions = p.page(1)
    except EmptyPage:
        transactions = p.page(p.num_pages)
    context = {
        "wallet":wallet,
        "totalTransactions":userTransactions.count(),
        "transactions":transactions
    }
    if transaction != '':
        context.update({
            "transaction":transaction
        })

    return render(request,'users/transaction-history.html',context)

# Transaction History
@login_required(login_url='login')
def getTransactionDetails(request,pk):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        try:
            transaction = Transaction.objects.get(id=pk,user=user)
            if transaction is not None:
                serializer = TransactionSerializer(transaction,many=False)
                return JsonResponse({
                    "code":"00",
                    'data':serializer.data
                })
        except ObjectDoesNotExist:
            return JsonResponse({
                "code":'09',
                "message":"Transaction not found"
            })
        

# Settings Page
@login_required(login_url='login')
def settingsPage(request):
    user = request.user
    pinSet = False
    try:
        transactionPIN = TransactionPIN.objects.get(user=user)
        if transactionPIN is not None:
            pinSet = True
    except ObjectDoesNotExist:
        pass

    
    context = {
        "pinSet":pinSet
    }
    return render(request,'users/settings.html',context)

@login_required(login_url='login')
def changePassword(request):
    user = request.user
    if is_ajax(request) and request.method == "POST":
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            # messages.success(request, 'Your password was successfully updated!')
            return JsonResponse({
                'code':'00'
            })
        else:            
            formErrors = form.errors.as_json()
            data = json.loads(formErrors)
            errorMessages = {}
            if 'old_password' in data:    
                errorList = data['old_password'][0]          
                errorMessages.update({
                    'old_password':errorList
                })
            if 'new_password2' in data:    
                errorList = data['new_password2'][0]          
                errorMessages.update({
                    'new_password2':errorList
                })
            return JsonResponse({
                'code':'09',
                'data':errorMessages,
            })
    else:
        return JsonResponse({
                'code':'09',
                'data':"Invalid request",
            })
    
# Wallet Page
@login_required(login_url='login')
def walletPage(request):
    user = request.user
    walletActivities = WalletFunding.objects.filter(user=user).order_by("-id")[:2]
    context = {
        "walletActivities":walletActivities,
    }

    # Dynamic account partner
    try:
        safeHavenDynamic = PartnerBank.objects.get(bank_name="SafeHaven MFB",status='Active')
        if safeHavenDynamic is not None:
            context.update({
                "dynamicAccount":safeHavenDynamic
            })
    except ObjectDoesNotExist:
        pass

    # Get SafeHaven Account Details
    if user.has_safeHavenAccount == True:
        safeHavenAccName = SafeHavenAccount.objects.get(user=user).account_name
        context.update({
                "safeHavenAccName":safeHavenAccName
            })



    
    return render(request,'users/wallet.html',context)

# One time payment amount
@login_required(login_url='login')
def dynamicAccountAmount(request):
    user = request.user
    if is_ajax(request) and request.method == "POST":
        depositAmount = request.POST.get("amount")
        accountBackend = DynamicAccountBackend.objects.get(name="Main")


        clientID = settings.SAFEH_CLIENT_ID
        clientAssertion = settings.SAFEH_CLIENT_ASSERTION
        authToken = ''
        ibsClientID = ''
        sweepAccount = settings.SAFEH_ACCOUNT_NUM

        transRef = reference(string_length=18)

        if accountBackend.active_backend == "SafeHaven MFB":
            # Generate Token
            url ='https://api.safehavenmfb.com/oauth2/token'                                        
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            payload = json.dumps({
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": clientAssertion,
            "client_id": clientID
            })
            response = requests.request("POST", url, headers=headers, data=payload)

            data = json.loads(response.text)

            if 'access_token' in data:
                authToken = data['access_token']
                # ibsClientID = data['ibs_client_id']
                # VERIFY TRANSACTION
                url = f"https://api.safehavenmfb.com/virtual-accounts"                                        
                headers = {
                    # 'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization':f"Bearer {authToken}",
                    'ClientID':clientID
                }

                payload = {
                    "validFor": 900,
                    "settlementAccount": {
                        "bankCode": "090286",
                        "accountNumber": sweepAccount
                    },
                    "amountControl": "Fixed",
                    "accountName": user.username,
                    # "callbackUrl": "https://5ae56adb4b7df7096b9be617cb24d53a.serveo.net/safehaven-onetime-webhook",                
                    "callbackUrl": "https://webhook.vuvu.ng/safehaven-onetime-webhook.php",
                    "amount": int(depositAmount),
                    "externalReference": transRef
                }
                
                
                response = requests.request("POST", url, headers=headers, json=payload)
                
                responseData = json.loads(response.text)
                if responseData['statusCode'] == 200:
                    accountDetails = responseData['data']
                    depositAccount = OneTimeDeposit.objects.create(
                        user = user,
                        accountNumber = accountDetails['accountNumber'],
                        accountName = accountDetails['accountName'],
                        transactionAmount = accountDetails['amount'],
                        accountID = accountDetails['_id'],
                        reference = accountDetails['externalReference'],
                    )
                    depositAccount.refresh_from_db()

                    bankData = PartnerBank.objects.get(bank_name="SafeHaven MFB")
                    transferCharges = bankData.deposit_charges
                    depositAmount = Decimal(depositAmount)
                    creditAmount = (depositAmount - (depositAmount * (transferCharges/100)))

                    return JsonResponse({
                        "code":"00",
                        "accountNumber":depositAccount.accountNumber,
                        "accountID":depositAccount.accountID,
                        "accountBackend":"SafeHaven",
                        "creditAmount":creditAmount,
                    })
                else:
                    return JsonResponse({
                        "code":"09",
                        "message":"Error generating account",
                    })
        
    return JsonResponse({
        "code":"09",
        "message":"Invalid request",
    })


@login_required(login_url='login')
def submitKYC(request):
    user = request.user
    if is_ajax(request=request) and request.method == 'POST':
        form = KYCDataForm(request.POST)
        if form.is_valid():
            idType = request.POST.get("id_type")
            idNum = request.POST.get("id_num")

            # BVN DATA
            if idType == "BVN" and user.bvn_verified == False:
                try:
                    idData = KYCData.objects.get(user=user,id_type=idType)
                    if idData is not None:
                        form = KYCDataForm(request.POST,instance=idData)
                        idData = form.save(commit=False)
                        
                        idData.dob = f"{request.POST.get('date-day')}-{request.POST.get('date-month')}-{request.POST.get('date-year')}"
                        idData.save()
                except ObjectDoesNotExist:
                    idData = form.save(commit=False)
                    idData.user = user
                    idData.dob = f"{request.POST.get('date-day')}-{request.POST.get('date-month')}-{request.POST.get('date-year')}"
                    idData.save()
           
            # NIN DATA
            if idType == "NIN" and user.nin_verified == False:
                try:
                    idData = KYCData.objects.get(id_type=idType)
                    if idData is not None:
                        form = KYCDataForm(request.POST,instance=idData)
                        idData = form.save(commit=False)                        
                        idData.dob = f"{request.POST.get('date-year')}-{request.POST.get('date-month')}-{request.POST.get('date-day')}"
                        idData.save()
                except ObjectDoesNotExist:
                    idData = form.save(commit=False)
                    idData.user = user
                    idData.dob = f"{request.POST.get('date-year')}-{request.POST.get('date-month')}-{request.POST.get('date-day')}"
                    idData.save()


            # Initiate ID verification
            clientID = settings.SAFEH_CLIENT_ID
            clientAssertion = settings.SAFEH_CLIENT_ASSERTION
            authToken = ''
            debitAccount = settings.SAFEH_DEBIT_ACCOUNT

            # Generate Token
            url ='https://api.safehavenmfb.com/oauth2/token'                                        
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }

            payload = json.dumps({
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": clientAssertion,
            "client_id": clientID
            })
            response = requests.request("POST", url, headers=headers, data=payload)

            data = json.loads(response.text)

            if 'access_token' in data:
                authToken = data['access_token']

                # SafeHaven reassign Account number
                url =f'https://api.safehavenmfb.com/identity/v2'                                        
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization':f"Bearer {authToken}",
                    'ClientID':clientID
                }

                payload = json.dumps({
                    "type": idType,
                    "async": False,
                    "number": idNum,
                    "debitAccountNumber": debitAccount,
                })
                response = requests.request("POST", url, headers=headers, data=payload)
                
                responseData = json.loads(response.text)
                if responseData['statusCode'] == 200: 
                    details = responseData['data']
                    return JsonResponse({
                        "code":"00",
                        "verificationID":details['_id']
                    })
                else:
                    return JsonResponse({
                        "code":"09",
                        "message":"Internal server error"
                    })
            else:
                    return JsonResponse({
                        "code":"09",
                        "message":"Internal server error"
                    })
        else:
            return JsonResponse({
                "code":"09"
            })
    else:
        return JsonResponse({
            "code":"09",
            "message":"Invalid Request",
        })
    


@login_required(login_url='login')
def validateKYC(request):
    user = request.user
    if is_ajax(request=request) and request.method == 'POST':
        verificationID = request.POST.get("verificationID")
        otpCode = request.POST.get("otp")
        idType = request.POST.get("identityType")

        idData = ''
        if idType == "BVN" and user.bvn_verified == False:
            try:
                kycInfo = KYCData.objects.get(user=user,id_type = idType)
                if kycInfo is not None:
                    idData = kycInfo
            except ObjectDoesNotExist:
                return JsonResponse({
                    "code":"01"
                })
        elif idType == "NIN" and user.nin_verified == False:
            try:
                kycInfo = KYCData.objects.get(user=user,id_type = idType)
                if kycInfo is not None:
                    idData = kycInfo
            except ObjectDoesNotExist:
                return JsonResponse({
                    "code":"01"
                })
            
        # Initiate ID verification
        clientID = settings.SAFEH_CLIENT_ID
        clientAssertion = settings.SAFEH_CLIENT_ASSERTION
        sweepAccount = settings.SAFEH_ACCOUNT_NUM
        authToken = ''
        # debitAccount = settings.SAFEH_DEBIT_ACCOUNT

        # Generate Token
        url ='https://api.safehavenmfb.com/oauth2/token'                                        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        payload = json.dumps({
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": clientAssertion,
        "client_id": clientID
        })
        response = requests.request("POST", url, headers=headers, data=payload)

        data = json.loads(response.text)

        if 'access_token' in data:
            authToken = data['access_token']

            # SafeHaven reassign Account number
            url =f'https://api.safehavenmfb.com/identity/v2/validate'                                        
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization':f"Bearer {authToken}",
                'ClientID':clientID
            }

            payload = json.dumps({
                "type": idType,
                "identityId": verificationID,
                "otp": otpCode,
            })
            response = requests.request("POST", url, headers=headers, data=payload)
            
            validationData = json.loads(response.text)
            if validationData['statusCode'] == 200:
                
                details = validationData['data']
                providerData = details['providerResponse']
                # id = providerData['firstName']
                idFirstName = providerData['firstName'].strip()
                idLastName = providerData['lastName'].strip()
                idDOB = providerData['dateOfBirth'].strip()
                identityId = details['_id']
                otpID = details['otpId']

                firstName = idData.first_name.upper().strip()
                lastName = idData.last_name.upper().strip()
                dob = idData.dob.strip()

                if (lastName == idLastName) and (firstName == idFirstName) and (dob == idDOB):
                    
                    
                    url ='https://api.safehavenmfb.com/accounts/v2/subaccount'
        
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization':f"Bearer {authToken}",
                        'ClientID':clientID
                    }

                    payload = json.dumps({ 
                        "phoneNumber": f"+234{user.phone_number}",
                        "emailAddress": user.email,
                        "identityType": "vID",
                        "autoSweep": True, 
                        "autoSweepDetails": {
                            "schedule": "Instant",
                            "accountNumber": sweepAccount
                        },
                        "externalReference": reference(string_length=16),
                        # "identityNumber": idData.id_num,
                        "identityId": identityId,
                        # "otp": otpCode,


                        # #######################
                        
                    })
                    response = requests.request("POST", url, headers=headers, data=payload)
                    
                    response = json.loads(response.text)
                    if response['statusCode'] == 200:
                        details = response['data']

                        if user.has_safeHavenAccount == False:

                            SafeHavenAccount.objects.create(
                                user = user,
                                account_number = details['accountNumber'],
                                account_name = details['accountName'],
                                account_id = details['_id'],
                                external_Reference = details['externalReference'],                        
                                )
                            user.bvn_verified = True
                            user.has_safeHavenAccount = True
                            user.safeHavenAccount_account_number = details['accountNumber'] 
                            user.safeHavenAccount_account_id = details['_id'] 
                            user.first_name = idData.first_name
                            user.last_name = idData.last_name
                            user.save()
                            idData.status = "Completed"
                            idData.save()
                            return JsonResponse({
                                'code':'00',
                                'message':"Account created successfully",
                                })
                        # else:
                        #     currentAccount = SafeHavenAccount.objects.get(user=user)
                        #     TempSafeHavenAccount.objects.create(
                        #         user = user,
                        #         account_number = currentAccount.account_number,
                        #         account_name = currentAccount.account_name,
                        #         account_id = currentAccount.account_id
                        #     )
                        #     currentAccount.delete()
                        #     # Create new account
                        #     SafeHavenAccount.objects.create(
                        #         user = user,
                        #         account_number = details['accountNumber'],
                        #         account_name = details['accountName'],
                        #         account_id = details['_id'],
                        #         external_Reference = details['externalReference'],                        
                        #         )
                        #     user.bvn_verified = True
                        #     user.has_safeHavenAccount = True
                        #     user.safeHavenAccount_account_number = details['accountNumber'] 
                        #     user.safeHavenAccount_account_id = details['_id'] 
                        #     user.save()
                        #     idData.status = "Completed"
                        #     idData.save()

                        #     return JsonResponse({
                        #         'code':'00',
                        #         'message':"Account created successfully",
                        #     })
                    
                    # Handle other endpoint errors
                    else:
                        return JsonResponse({
                            'code':'09',
                            'message':f"ERR:{response['statusCode']} {response['message']}",
                        })
                
                else:
                    return JsonResponse({
                        "code":"09",
                        "message":"Identity data does not match"
                    })
                
            # Handles wrong OTP
            elif validationData['statusCode'] == 400:
                return JsonResponse({
                    "code":"09",
                    "message":"Invalid OTP"
                })
            
            else:
                return JsonResponse({
                    'code':'09',
                    'message':f"ERR:{response['statusCode']} {response['message']}",
                })
        else:
            return JsonResponse({
                'code':'09',
                'message':f"ERR:{data['statusCode']} account could not be created at the moment, please try again in few minutes",
            })
        

@login_required(login_url='login')
def redeemCashback(request):
    user = request.user
    if is_ajax(request=request) and request.method == 'GET':
        bonusType = request.GET.get('type')
        wallet = UserWallet.objects.get(user=user)
        amount = wallet.cashback
        balanceBefore = wallet.balance
        totalFunded = user.total_wallet_funding
        if bonusType == 'cashback' and amount > 0:
            wallet.balance += amount
            wallet.cashback = 0
            wallet.save()
            # Create wallet Activity
            WalletActivity.objects.create(
                user = user,
                event_type = "Credit",
                transaction_type = "Cashback Withdrwal",
                comment = "Cashback",
                amount = amount,
                balanceBefore = balanceBefore,
                balanceAfter = wallet.balance,
            )

            # Create wallet 
            WalletFunding.objects.create(
                user = user,
                method = "Cashback",
                amount = amount,
                balanceBefore = balanceBefore,
                balanceAfter = wallet.balance,
                sessionId = "Cashback Withdrawal",
                accountNumber = "0000",
                sourceAccountNumber = "Vuvu",
                sourceAccountName = "Vuvu Cashback",
            )
            return JsonResponse({
                'code':'00',
                'balance':wallet.balance,
                'bonusBalance':wallet.cashback,               
            })
        else:
           return JsonResponse({
                'code':'09',               
            }) 
    else:
        return JsonResponse({
                'code':'09',               
            })
    

# Support Page
@login_required(login_url='login')
def supportPage(request):
    user = request.user

    
    # context = {
    #     "pinSet":pinSet
    # }
    return render(request,'users/support.html')

# Notifications Page
@login_required(login_url='login')
def notificationsPage(request):
    user = request.user
    userNotificationsRaw = Notifications.objects.filter(user=user).order_by("-id")
    userNotificationsRaw.update(status="Read")
    context = {
        "totalNotifications":userNotificationsRaw.count(),
        "notifications":userNotificationsRaw
    }
    return render(request,'users/notifications.html',context)

# Notifications Page
@login_required(login_url='login')
def deleteNotifications(request):
    user = request.user
    userNotifications = Notifications.objects.filter(user=user)
    userNotifications.delete()
    return redirect("notifications")

# Delete Account Page
@login_required(login_url='login')
def deleteAccountPage(request):
    user = request.user
    deleteQueue = None
    try:
        deleting = AccountDeleteQueue.objects.get(user=user)
        if deleting is not None:
            deleteQueue = deleting
    except ObjectDoesNotExist:
        pass
    context = {
        "deleteQueue":deleteQueue
    }

    
    # context = {
    #     "pinSet":pinSet
    # }
    return render(request,'users/delete-account.html',context)

# Delete User Account request
@login_required(login_url='login')
def deleteAccount(request):
    user = request.user
    # account = User.objects.get(id=user.id)
    # Delete Date
    today = datetime.today()
    deleteDate = today + timedelta(days=2)
    try:
        deleteQueue = AccountDeleteQueue.objects.get(user=user)
        if deleteQueue is not None:
            return redirect('delete-account')
    except ObjectDoesNotExist:        
        AccountDeleteQueue.objects.create(
            user = user,
            event_date = deleteDate
        )
    return redirect ('delete-account')

# Cancel account delete
@login_required(login_url='login')
def cancelAccountDelete(request):
    user = request.user
    try:
        deleteRequest = AccountDeleteQueue.objects.get(user=user)
        if deleteRequest is not None:
            deleteRequest.delete()
    except:
        pass

    return redirect('delete-account')


# Stories Page
@login_required(login_url='login')
def storiesPage(request):
    user = request.user

    
    context = {
    }
    return render(request,'users/stories.html',context)

# Stories Page
@login_required(login_url='login')
def watchStories(request):
    user = request.user
    storiesRaw = VuvuStory.objects.all().order_by("-id")
    if storiesRaw.count() > 0:
        recentStory = storiesRaw.first()
        storiesRaw = storiesRaw.exclude(id=recentStory.id)

    p = Paginator(storiesRaw,10)
    page_number = request.GET.get('page')
    try:
        stories = p.get_page(page_number)
    except PageNotAnInteger:
        stories = p.page(1)

    except EmptyPage:
        stories = p.page(p.num_pages)

    
    context = {
        "stories":stories,
        "totalStories":storiesRaw.count(),
        "recentStory":recentStory,
    }
    return render(request,'users/watch-stories.html',context)

# Submit story Page
@login_required(login_url='login')
def submitStory(request):
    user = request.user
    if request.method == "POST":
        form = StoryForm(request.POST)
        if form.is_valid():
            newStory = form.save(commit=False)
            newStory.user = user
            newStory.save()
            newStory.refresh_from_db()
            # imagesForm  = ImagesForm(request.POST, request.FILES)
            images = request.FILES.getlist('file_field')
            
            if len(images) > 0:
                with tempfile.TemporaryDirectory() as temp_dir:
                    for uploaded_file in images:
                        file_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(file_path, 'wb') as file:
                            for chunk in uploaded_file.chunks():
                                file.write(chunk)

                    zip_file_path = os.path.join(temp_dir, 'new.zip')
                    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                        for uploaded_file in images:
                            file_path = os.path.join(temp_dir, uploaded_file.name)
                            zip_file.write(file_path, uploaded_file.name)

                    with open(zip_file_path, 'rb') as zip_file:
                        # Create a ZipFileModel instance and save the zip file into the database
                        zip_model = ZipFileModel()
                        zip_model.file.save(f'{user.username}_{newStory.created}.zip', File(zip_file))
                        zip_model.save()
                        newStory.image_files = zip_model.file
                        newStory.save()
                
            messages.success(request,"success")
            
            # files = imageForm.cleaned_data["file_field"]
            # print(imageForm)
            return redirect("tell-your-story")
        else:
            return redirect("tell-your-story")
    
    context = {
    }
    return render(request,'users/submit-story.html',context)





        


        
        


