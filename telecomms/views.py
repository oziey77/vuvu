from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from django.core.exceptions import ObjectDoesNotExist

from adminbackend.models import AirtimeBackend, AirtimeDiscount, DataBackend
from telecomms.models import ATNDataPlans, AirtimeServices, DataServices, HonouworldDataPlans, Twins10DataPlans
from telecomms.serializers import ATNDataPlanSerializer, AirtimeDiscountSerializer, HonouworldDataPlanSerializer, Twins10DataPlanSerializer
from users.models import Cashback, Transaction, TransactionPIN, UserWallet, WalletActivity
from vuvu.custom_functions import is_ajax, reference
from django.contrib.auth.hashers import check_password

from datetime import datetime, timedelta

# Create your views here.

# API KEYS
# ATN
airtimeNigeriaAPI = 'Bearer '+ settings.AIRTIME_NG
# Honourworld
honourAPIKey = f'Bearer {settings.HONOUR_API_KEY}'
# Twins10
apiToken = settings.TWINS10_TOKEN


# Airtime Page 
@login_required(login_url='login')
def airtimePage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    context = {
        'mainBalance':wallet.balance
    }
    return render(request,'telecomms/airtime.html',context)


@login_required(login_url='login')
def getAirtimeDiscount(request):
    if is_ajax(request) and request.method == "GET":
        airtimeDiscounts = AirtimeDiscount.objects.all()
        serializer = AirtimeDiscountSerializer(airtimeDiscounts,many=True)
        return JsonResponse({
            "code":'00',
            'data':serializer.data
        })


# Ajax call to buy airtime
@login_required(login_url='login')
def buyAirtime(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        transcationPin = request.POST.get('transcationPin')
        transPin = TransactionPIN.objects.get(user=user)
        if check_password(transcationPin,transPin.transaction_pin):       
        
            if totalWalletFunding > 0:
                operator = request.POST.get('operator')
                recipient = request.POST.get('recipient')
                amount = Decimal(request.POST.get('amount'))
                wallet = UserWallet.objects.get(user=user)  

                airtimeServices = AirtimeServices.objects.get(network_operator=operator)
                if airtimeServices.available == False:
                    return JsonResponse({
                        "code":"09",
                        "message":f"{operator} airtime is currently unavailable"
                    }) 


                # First Check for duplicate transaction 
                existingTran = Transaction.objects.filter(user=user,operator=operator,recipient=recipient,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
                if existingTran.count() > 0:
                    return JsonResponse({
                        "code":"09",
                        "message":"Duplicate transaction wait 1 minute"
                    })          
                        
                
                # Check if user has enough balance
                if amount > 0 and amount <= wallet.balance:
                    balanceBefore = wallet.balance
                    wallet.balance -= amount
                    wallet.save()
                    
                    transRef = reference(26)
                    try:
                        existing = Transaction.objects.get(reference=transRef)
                        while existing is not None:
                            transRef = reference(6)
                            existing = Transaction.objects.get(reference=transRef)
                    except ObjectDoesNotExist:
                        # Set user referral  codes and create wallet
                        pass

                    # Create wallet Activity
                    WalletActivity.objects.create(
                        user = user,
                        event_type = "Debit",
                        transaction_type = "Airtime",
                        comment = f"Airtime {transRef}",
                        amount = Decimal(amount),
                        balanceBefore = balanceBefore,
                        balanceAfter = wallet.balance,
                    )
                    # Create Transaction Record
                    transaction = Transaction.objects.create(
                                    user = user,
                                    operator = operator,
                                    transaction_type = "Airtime",
                                    recipient = recipient,
                                    reference = transRef,
                                    package = f"{operator} VTU",
                                    amount = amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )
                    
                    transaction.refresh_from_db()

                    user.last_transacted = datetime.now().date()
                    user.save()

                    # Second check for duplicate transaction
                    startTime = datetime.now() - timedelta(seconds=30) 
                    existingTran = Transaction.objects.filter(user=user,operator=operator,recipient=recipient,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
                    if existingTran.count() > 1:
                        return JsonResponse({
                            "code":"09",
                            "message":"Duplicate transaction wait 1 minute"
                        })
                    else:
                        airtimeBackend = AirtimeBackend.objects.get(operator=operator)
                        
                        # Buy from ATN Backend
                        if airtimeBackend.active_backend == "ATN":
                            transaction.APIBackend = 'ATN'
                            transaction.save()
                            url = 'https://www.airtimenigeria.com/api/v1/airtime/purchase'
                            
                            payload = {
                                "network_operator": operator,
                                "phone": recipient,
                                "amount": str(amount),
                                "customer_reference": transRef,
                                # "callback_url": callBackUrl,
                                }
                            headers = {
                                'Authorization': airtimeNigeriaAPI,
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                                }

                            response = requests.request('POST', url, headers=headers, json=payload)
                            data = response.json()
                            
                            if data['success'] == True:
                                # calculate Discount/cashback
                                airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                                discountRate = airtimeDiscount.rate
                                calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                                Cashback.objects.create(
                                    user = user,
                                    transaction_type = 'Airtime',
                                    message = f"Airtime {transaction.reference}",
                                    amount = calculatedDiscount
                                )
                                wallet.cashback += calculatedDiscount
                                wallet.save()


                                transaction.status = "Success"
                                transaction.discount = calculatedDiscount
                                transaction.message = "Transaction successful"
                                transaction.APIreference = data['details']['reference']
                                transaction.save()                    
                                return JsonResponse({
                                    'code':'00',        
                                })
                            else:
                                transaction.status = "Refunded"
                                transaction.message = "Transaction refunded"
                                transaction.refunded = True
                                transaction.save()

                                balanceBefore = wallet.balance
                                wallet.balance += transaction.amount
                                wallet.save()

                                # Create wallet Activity
                                WalletActivity.objects.create(
                                    user = user,
                                    event_type = "Credit",
                                    transaction_type = "Airtime",
                                    comment = f"Airtime {transRef} Refund",
                                    amount = transaction.amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )

                                return JsonResponse({
                                    "code":"09",
                                    "message":data['message']
                                })
                        elif airtimeBackend.active_backend == "TWINS10":
                            transaction.APIBackend = 'TWINS10'
                            transaction.save()
                            if operator == "MTN":
                                networkID = "1"
                            elif operator == "Airtel":
                                networkID = "2"
                            elif operator == "Glo":
                                networkID = "3"
                            elif operator == "9Mobile":
                                networkID = "4"

                            # API ENDPOINT for AIRTIME     
                            url = 'https://twins10.com/api/topup/'

                            payload = {
                                        "plan_type":"VTU",
                                        "amount":str(amount),
                                        "network": networkID,
                                        "phone":recipient,
                                        "bypass":False,
                                        "request-id":transRef                  
                                    }
                            headers = {
                                        'Authorization': f"Token {apiToken}",
                                        'Accept': 'application/json'
                                    }

                            response = requests.request('POST', url, headers=headers, json=payload)
                            
                            
                            # data = json.loads(response.text)
                            airtimeDetails = response.json()
                            
                            APIResponse = ''
                            if 'response' in airtimeDetails:
                                    APIResponse = airtimeDetails["response"]
                            elif 'message' in airtimeDetails:
                                APIResponse = airtimeDetails["message"]
                        
                            if airtimeDetails['status'] == "success" or airtimeDetails['status'] == "processing" or airtimeDetails['status'] == "Processing":
                                # calculate Discount/cashback
                                airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                                discountRate = airtimeDiscount.rate
                                calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                                Cashback.objects.create(
                                    user = user,
                                    transaction_type = 'Airtime',
                                    message = f"Airtime {transaction.reference}",
                                    amount = calculatedDiscount
                                )
                                wallet.cashback += calculatedDiscount
                                wallet.save()


                                transaction.status = "Success"
                                transaction.discount = calculatedDiscount
                                transaction.message = "Transaction successful"
                                transaction.APIreference = transRef
                                transaction.save()                    
                                return JsonResponse({
                                    'code':'00',        
                                })
                            elif airtimeDetails['status'] == "fail":
                                transaction.status = "Refunded"
                                transaction.message = "Transaction refunded"
                                transaction.refunded = True
                                transaction.save()

                                balanceBefore = wallet.balance
                                wallet.balance += transaction.amount
                                wallet.save()

                                # Create wallet Activity
                                WalletActivity.objects.create(
                                    user = user,
                                    event_type = "Credit",
                                    transaction_type = "Airtime",
                                    comment = f"Airtime {transRef} Refund",
                                    amount = transaction.amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )

                                return JsonResponse({
                                    "code":"09",
                                    "message":APIResponse
                                })
                        elif airtimeBackend.active_backend == "HONOURWORLD": 
                            transaction.APIBackend = 'HONOURWORLD'
                            transaction.save()
                            url = 'https://vtuapi.honourworld.com/api/v2/airtime/buy'
                            payload = {
                                    "network": operator.upper(),
                                    "phone": recipient,
                                    "amount": str(amount),
                                    # "max_amount": 5000,
                                    # "callback_url": "https://webhook.site/f4e6022a-5f36-4f43-aba3-fb8419ca6b63"
                                    }
                            headers = {
                                    'Authorization': honourAPIKey,
                                    # 'Content-Type': 'application/json',
                                    # 'Accept': 'application/json'
                                    }

                            response = requests.request('POST', url, headers=headers, json=payload)
                            responseDetails = response.json()

                            if 'data' in responseDetails and responseDetails['data']['code'] == 200:
                                # calculate Discount/cashback
                                airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                                discountRate = airtimeDiscount.rate
                                calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                                Cashback.objects.create(
                                    user = user,
                                    transaction_type = 'Airtime',
                                    message = f"Airtime {transaction.reference}",
                                    amount = calculatedDiscount
                                )
                                wallet.cashback += calculatedDiscount
                                wallet.save()


                                transaction.status = "Success"
                                transaction.discount = calculatedDiscount
                                transaction.message = "Transaction successful"
                                transaction.APIreference = responseDetails['data']['reference']
                                transaction.save()                    
                                return JsonResponse({
                                    'code':'00',        
                                })
                            else:
                                error = responseDetails['error'][0]
                                transaction.status = "Refunded"
                                transaction.message = "Transaction refunded"
                                transaction.refunded = True
                                transaction.save()

                                balanceBefore = wallet.balance
                                wallet.balance += transaction.amount
                                wallet.save()

                                # Create wallet Activity
                                WalletActivity.objects.create(
                                    user = user,
                                    event_type = "Credit",
                                    transaction_type = "Airtime",
                                    comment = f"Airtime {transRef} Refund",
                                    amount = transaction.amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )

                                return JsonResponse({
                                    "code":"09",
                                    "message":error["msg"]
                                })
            else:       
                return JsonResponse({
                    "code":"09",
                    "message":"No funding history found for your account"
                })
        else:
            return JsonResponse({
                "code":"01",
                "message":"Invalid transaction PIN"
            })
    return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })


# Airtime Page 
@login_required(login_url='login')
def dataPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    context = {
        'mainBalance':wallet.balance
    }
    return render(request,'telecomms/data.html',context)


@login_required(login_url='login')
def fetchDataPlans(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        operator = request.GET.get('operator')
        databackend = DataBackend.objects.get(operator=operator)
        activebackend = databackend.active_backend
        dataService = DataServices.objects.get(network_operator=operator)
        if dataService.available == False:
            return JsonResponse({
                "code":"09",
                "message":f"{operator} data plans are currently unavailable",
            })
        else:
            if activebackend == "ATN":
                dataplans = ATNDataPlans.objects.filter(network_operator=operator).order_by("id")
                serializer = ATNDataPlanSerializer(dataplans,many=True)
                return JsonResponse({
                    "code":"00",
                    "activeBackend":activebackend,
                    "plans":serializer.data,
                })
            elif activebackend == "HONOURWORLD":
                dataplans = HonouworldDataPlans.objects.filter(network_operator=operator).order_by("id")
                serializer = HonouworldDataPlanSerializer(dataplans,many=True)
                return JsonResponse({
                    "code":"00",
                    "activeBackend":activebackend,
                    "plans":serializer.data,
                })
            elif activebackend == "TWINS10":
                dataplans = Twins10DataPlans.objects.filter(network_operator=operator).order_by("id")
                serializer = Twins10DataPlanSerializer(dataplans,many=True)
                return JsonResponse({
                    "code":"00",
                    "activeBackend":activebackend,
                    "plans":serializer.data,
                })
            

# Ajax call to buy airtime
@login_required(login_url='login')
def buyData(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST":   
        transcationPin = request.POST.get('transcationPin')
        transPin = TransactionPIN.objects.get(user=user)
        if check_password(transcationPin,transPin.transaction_pin):

            if totalWalletFunding > 0:
                operator = request.POST.get('operator')
                recipient = request.POST.get('recipient')
                planID = request.POST.get('planID')
                
                
                wallet = UserWallet.objects.get(user=user)  

                dataServices = DataServices.objects.get(network_operator=operator)
                if dataServices.available == False:
                    return JsonResponse({
                        "code":"09",
                        "message":f"{operator} Data is currently unavailable"
                    })
                else:
                    dataBackend = DataBackend.objects.get(operator=operator)
                    activeBackend = dataBackend.active_backend
                    selectedPlan = '' 
                    if activeBackend == "ATN":
                        try:
                            plan = ATNDataPlans.objects.get(package_id=planID)
                            if plan is not None:
                                selectedPlan = plan
                        except ObjectDoesNotExist:
                            return JsonResponse({
                            'code':'09', 
                            'message':'selected plan is not valid'       
                        })
                    if activeBackend == "ATN":
                        try:
                            plan = ATNDataPlans.objects.get(package_id=planID)
                            if plan is not None:
                                selectedPlan = plan
                        except ObjectDoesNotExist:
                            return JsonResponse({
                            'code':'09', 
                            'message':'selected plan is not valid'       
                        })
                    elif activeBackend == "HONOURWORLD":
                        try:
                            plan = HonouworldDataPlans.objects.get(package_id=planID)
                            if plan is not None:
                                selectedPlan = plan
                        except ObjectDoesNotExist:
                            return JsonResponse({
                            'code':'09', 
                            'message':'selected plan is not valid'       
                        })
                    elif activeBackend == "TWINS10":
                        try:
                            plan = Twins10DataPlans.objects.get(package_id=planID)
                            if plan is not None:
                                selectedPlan = plan
                        except ObjectDoesNotExist:
                            return JsonResponse({
                            'code':'09', 
                            'message':'selected plan is not valid'       
                        })

                    existingTran = Transaction.objects.filter(user=user,operator=operator,recipient=recipient,package=selectedPlan.plan,created__gte=datetime.now() - timedelta(seconds=45))
                    if existingTran.count() > 0:
                        return JsonResponse({
                            "code":"09",
                            "message":"Duplicate transaction wait 1 minute"
                        })

                    # Check if user has enough balance to make purchase
                    if selectedPlan.price <= wallet.balance:
                        balanceBefore = wallet.balance
                        wallet.balance -= selectedPlan.price
                        wallet.save()

                        # Generate transaction reference
                        transRef = reference(26)
                        # Create wallet Activity
                        WalletActivity.objects.create(
                            user = user,
                            event_type = "Debit",
                            transaction_type = "Data",
                            comment = f"Data {transRef}",
                            amount = selectedPlan.price,
                            balanceBefore = balanceBefore,
                            balanceAfter = wallet.balance,
                        )
                        # Create Transaction Record
                        transaction = Transaction.objects.create(
                                        user = user,
                                        operator = operator,
                                        transaction_type = "Data",
                                        recipient = recipient,
                                        reference = transRef,
                                        package = selectedPlan.plan,
                                        amount = selectedPlan.price,
                                        balanceBefore = balanceBefore,
                                        balanceAfter = wallet.balance,
                                    )
                        
                        transaction.refresh_from_db()
                        user.last_transacted = datetime.now().date()
                        user.save()

                        existingTran = Transaction.objects.filter(user=user,operator=operator,recipient=recipient,package=selectedPlan.plan,created__gte=datetime.now() - timedelta(seconds=45))
                        if existingTran.count() > 1:
                            return JsonResponse({
                                "code":"09",
                                "message":"Duplicate transaction wait 1 minute"
                            })

                        if activeBackend == "ATN":
                            transaction.APIBackend = 'ATN'
                            transaction.save()
                            # callBackUrl = "https://webhook.yagapay.io/atn-webhook.php"
                            # API ENDPOINT for AIRTIME     
                            url = 'https://www.airtimenigeria.com/api/v1/data/purchase'
                            payload = {
                                    "network_operator": operator,
                                    "phone": recipient,
                                    "package_code": selectedPlan.package_id,
                                    "customer_reference": transRef, 
                                    # "callback_url": callBackUrl,                   
                                    }
                            headers = {
                                    'Authorization': airtimeNigeriaAPI,
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json'
                                    }

                            response = requests.request('POST', url, headers=headers, json=payload)
                            data = response.json()
                            

                            if data['success'] == True:
                                Cashback.objects.create(
                                    user = user,
                                    transaction_type = 'Data',
                                    message = f"Data {transaction.reference}",
                                    amount = Decimal(5)
                                )
                                wallet.cashback += Decimal(5)
                                wallet.save()


                                transaction.status = "Success"
                                transaction.discount = Decimal(5)
                                transaction.message = "Transaction successful"
                                transaction.APIreference = data['details']['reference']
                                transaction.save()                    
                                return JsonResponse({
                                    'code':'00',        
                                })
                            else:
                                transaction.status = "Refunded"
                                transaction.message = "Transaction refunded"
                                transaction.refunded = True
                                transaction.save()

                                balanceBefore = wallet.balance
                                wallet.balance += transaction.amount
                                wallet.save()

                                # Create wallet Activity
                                WalletActivity.objects.create(
                                    user = user,
                                    event_type = "Credit",
                                    transaction_type = "Data",
                                    comment = f"Data {transRef} Refund",
                                    amount = transaction.amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )

                                return JsonResponse({
                                    "code":"09",
                                    "message":data['message']
                                })
                        elif activeBackend == "HONOURWORLD": 
                            transaction.APIBackend = 'HONOURWORLD'
                            transaction.save()
                            url = 'https://vtuapi.honourworld.com/api/v2/data/buy'
                            payload = {
                                    "network": operator.upper(),
                                    "phone": recipient,
                                    "planId": selectedPlan.package_id,
                                    # "max_amount": 5000,
                                    # "callback_url": "https://webhook.site/f4e6022a-5f36-4f43-aba3-fb8419ca6b63"
                                    }
                            headers = {
                                    'Authorization': honourAPIKey,
                                    # 'Content-Type': 'application/json',
                                    # 'Accept': 'application/json'
                                    }

                            response = requests.request('POST', url, headers=headers, json=payload)
                            
                            data = response.json()
                            

                            if data['code'] == 200:
                                Cashback.objects.create(
                                    user = user,
                                    transaction_type = 'Data',
                                    message = f"Data {transaction.reference}",
                                    amount = Decimal(5)
                                )
                                wallet.cashback += Decimal(5)
                                wallet.save()
                                
                                # Update transaction
                                transaction.status = "Success"
                                transaction.discount = Decimal(5)
                                transaction.message = "Transaction successful"
                                transaction.APIreference = data['data']['reference']
                                transaction.save()                    
                                return JsonResponse({
                                    'code':'00',        
                                })
                            else:
                                error = data['error'][0]
                                transaction.status = "Refunded"
                                transaction.message = "Transaction refunded"
                                transaction.refunded = True
                                transaction.save()

                                balanceBefore = wallet.balance
                                wallet.balance += transaction.amount
                                wallet.save()

                                # Create wallet Activity
                                WalletActivity.objects.create(
                                    user = user,
                                    event_type = "Credit",
                                    transaction_type = "Data",
                                    comment = f"Data {transRef} Refund",
                                    amount = transaction.amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )

                                return JsonResponse({
                                    "code":"09",
                                    "message":error["msg"]
                                })
                        elif activeBackend == "TWINS10":
                            transaction.APIBackend = 'TWINS10'
                            transaction.save() 
                            if operator == "MTN":
                                networkID = "1"
                            elif operator == "Airtel":
                                networkID = "2"
                            elif operator == "Glo":
                                networkID = "3"
                            elif operator == "9Mobile":
                                networkID = "4"

                            url = 'https://twins10.com/api/data'
                            payload = {
                                        "network": networkID,
                                        "phone":recipient,
                                        "data_plan":selectedPlan.package_id,
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
                                Cashback.objects.create(
                                    user = user,
                                    transaction_type = 'Data',
                                    message = f"Data {transaction.reference}",
                                    amount = Decimal(5)
                                )
                                wallet.cashback += Decimal(5)
                                wallet.save()
                                
                                # Update transaction
                                transaction.status = "Success"
                                transaction.discount = Decimal(5)
                                transaction.message = "Transaction successful"
                                transaction.APIreference = transRef
                                transaction.save()                    
                                return JsonResponse({
                                    'code':'00',        
                                })
                            elif data['status'] == "fail":
                                transaction.status = "Refunded"
                                transaction.message = "Transaction refunded"
                                transaction.refunded = True
                                transaction.save()

                                balanceBefore = wallet.balance
                                wallet.balance += transaction.amount
                                wallet.save()

                                # Create wallet Activity
                                WalletActivity.objects.create(
                                    user = user,
                                    event_type = "Credit",
                                    transaction_type = "Data",
                                    comment = f"Data {transRef} Refund",
                                    amount = transaction.amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )

                                if 'response' in data:
                                    APIResponse = data["response"]
                                elif 'message' in data:
                                    APIResponse = data["message"]

                                return JsonResponse({
                                    "code":"09",
                                    "message":APIResponse
                                })
            
            else:
                return JsonResponse({
                    "code":"09",
                    "message":"No funding history found for your account"
                })
        else:
            return JsonResponse({
                "code":"01",
                "message":"Invalid transaction PIN"
            })
    return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })