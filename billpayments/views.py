from django.shortcuts import render
from decimal import Decimal
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from django.core.exceptions import ObjectDoesNotExist

from adminbackend.models import BillServicesDiscount, CableBackend, EPINBackend, ElectricityBackend
from billpayments.models import BillPaymentServices
from users.models import Beneficiary, Transaction, UserWallet, WalletActivity
from vuvu.custom_functions import is_ajax, reference

from datetime import datetime, timedelta


# Electricity Page 
@login_required(login_url='login')
def electricityPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)

    electricityDiscount = BillServicesDiscount.objects.get(service_type='Electricity').rate
    # Electricity Beneficiary
    electricityBackend = ElectricityBackend.objects.get(name='Main')
    electricityBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            electricityBeneficiaries = userBeneficiaries.electricity
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'electricityBeneficiaries':electricityBeneficiaries,
        'electricityBackend':electricityBackend,
        'electricityDiscount':electricityDiscount,
    }
    return render(request,'billpayments/electricity.html',context)

# Validate Meter  
@login_required(login_url='login')
def validateMeter(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        meterNumber = request.GET.get("meterNumber")
        selectedOperator = request.GET.get("selectedOperator")
        meterType = request.GET.get("meterType")
        amount = request.GET.get("amount")

        electricityAvailable = BillPaymentServices.objects.get(service_type="Electricity").available

        if electricityAvailable:
            electricityBackend = ElectricityBackend.objects.get(name='Main').active_backend
            
            if electricityBackend == "9Payment":
                # API CALL to validate meter

                # Remove temp API KEY
                APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODA4NjY5OSwianRpIjoiMGNkYjMxY2YtNjNlYy00NDM1LWE3NzQtY2FmMDVkMTAzYjA5IiwiZXhwIjoxNzI4MDkzODk5fQ.z1SAlWhnY8T83XO8RUHf1q_12hhLCTYs_aq73JjqHhaGCSmzq3nYv7DoLcYHGZrboJ4EbOM8Vf29LyD6yc_PmA"
                # END of remove
                url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/validate'
                payload = {
                        "customerId": meterNumber,
                        "amount": str(amount),
                        "billerId": selectedOperator,
                        "itemId": meterType,
                        }
                headers = {
                        'Authorization': f"Bearer {APIKEY}",
                        # 'Content-Type': 'application/json',
                        # 'Accept': 'application/json'
                        }

                response = requests.request('POST', url, headers=headers, json=payload)
                responseDetails = response.json()
                if responseDetails['responseCode'] == '200':
                    customerData = responseDetails['data']
                    return JsonResponse({
                        "code":"00",
                        "customerName":customerData['customerName'],
                        "address":customerData['otherField'],
                        "amount":customerData['amount'],
                        'backend':"9Payment", 
                    })
                if responseDetails['responseCode'] == '400':
                    return JsonResponse({
                        "code":"09",
                        "message":"Invalid meter number"
                    })
            elif electricityBackend == "SafeHaven":
                clientID = settings.SAFEH_CLIENT_ID
                clientAssertion = settings.SAFEH_CLIENT_ASSERTION
                authToken = ''
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
                    # VERIFY METER
                    url = "https://api.safehavenmfb.com/vas/verify"                                        
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization':f"Bearer {authToken}",
                        'ClientID':clientID
                    }

                    
                    payload = json.dumps({
                        "serviceCategoryId": selectedOperator,
                        "entityNumber": meterNumber
                    })
                    responseData = requests.request("POST", url, headers=headers, data=payload)
                    
                    
                    responseData = json.loads(responseData.text)
                    if responseData['statusCode'] == 200:
                        customerDetails = responseData['data']
                        if customerDetails["vendType"] != meterType.upper():
                            return JsonResponse({
                            "code":"09",
                            "message":"wrong meter type selected"
                            })
                        else:
                            return JsonResponse({
                                "code":"00",
                                "customerName":customerDetails["name"],
                                "address":customerDetails["address"],
                                "amount":amount,
                                'backend':"SafeHaven",    
                            })
                    else:
                        return JsonResponse({
                            "code":"09",
                            "message":responseData['message']
                        })
        else:
            return JsonResponse({
                'code': '09',
                'message': "electricity payment is currently unavailable",
            })
    else:
        return JsonResponse({
            "code":"09",
            "message":"invalid request"
        })
        


# Ajax call to buy Electricity
@login_required(login_url='login')
def buyElectricity(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding
    wallet = UserWallet.objects.get(user=user) 
    lifetimeDiscount = user.discount_genarated
    successfulTransactions = user.successful_transaction_value
    # Get user wallet
    wallet = UserWallet.objects.get(user=user)

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            if (wallet.balance ) > (((totalWalletFunding + (lifetimeDiscount)) - successfulTransactions) + (Decimal(100))):
                user.can_perform_transaction = False
                user.save()
                return JsonResponse({
                    "code":"09",
                    "message":f"internal server error"
                })
            meterNumber = request.POST.get("meterNumber")
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            meterType = request.POST.get("meterType")
            itemId = request.POST.get("itemId")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            saveBeneficiary = request.POST.get('saveBeneficiary')
            
            

            # Safe Beneficiary Logic
            if saveBeneficiary == "on":
                try:
                    userBeneficiaries = Beneficiary.objects.get(user=user)
                    if userBeneficiaries is not None:
                        electricityBeneficiary = userBeneficiaries.electricity 
                        # Search of record already exist
                        alreadySaved = False
                        for entry in electricityBeneficiary:
                            # alreadySaved = True
                            if entry['meterNum'] == meterNumber:
                                alreadySaved = True
                                break
                        # If rececipient has not been saved before
                        if alreadySaved == False:
                            electricityBeneficiary.append(
                                {
                                    "operator":selectedOperatorName,
                                    "meterNum":meterNumber,
                                    "customerName":customerName,
                                    "meterType":meterType,
                                }
                            ) 
                            userBeneficiaries.electricity = electricityBeneficiary 
                            userBeneficiaries.save() 
                        
                except ObjectDoesNotExist:
                    newBeneficiary = [{
                        "operator":selectedOperatorName,
                        "meterNum":meterNumber,
                        "customerName":customerName,
                        "meterType":meterType,
                        }]
                    # Create Beficiaryobject
                    Beneficiary.objects.create(
                        user = user,
                        electricity = newBeneficiary
                    )
            


            # duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
            if existingTran.count() > 0:
                return JsonResponse({
                    "code":"09",
                    "message":"Please wait 1 minute"
                })          
                    
            
            # Check if user has enough balance
            if amount > 0 and amount <= wallet.balance:
                electricityDiscount = BillServicesDiscount.objects.get(service_type='Electricity').rate
                calculatedDiscount = Decimal((amount * electricityDiscount) / Decimal(100.00))
                electricityAmount = amount
                amount = amount - calculatedDiscount
                user.discount_genarated += calculatedDiscount   
                balanceBefore = wallet.balance
                wallet.balance -= amount
                wallet.save()
                user.save()
                
                transRef = reference(25)
                try:
                    existing = Transaction.objects.get(reference=transRef)
                    while existing is not None:
                        transRef = reference(25)
                        existing = Transaction.objects.get(reference=transRef)
                except ObjectDoesNotExist:
                    # Set user referral  codes and create wallet
                    pass

                # Create wallet Activity
                WalletActivity.objects.create(
                    user = user,
                    event_type = "Debit",
                    transaction_type = "Electricity",
                    comment = f"Electricity {transRef}",
                    amount = amount,
                    balanceBefore = balanceBefore,
                    balanceAfter = wallet.balance,
                )
                # Create Transaction Record
                transaction = Transaction.objects.create(
                    user = user,
                    operator = selectedOperatorName,
                    transaction_type = "Electricity",
                    recipient = meterNumber,
                    reference = transRef,
                    package = meterType,
                    amount = amount,
                    discount = calculatedDiscount,
                    unit_cost = electricityAmount,
                    balanceBefore = balanceBefore,
                    balanceAfter = wallet.balance,
                )
    
                transaction.refresh_from_db()

                user.last_transacted = datetime.now().date()
                user.save()

                # Second check for duplicate transaction
                startTime = datetime.now() - timedelta(seconds=30) 
                existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
                if existingTran.count() > 1:
                    return JsonResponse({
                        "code":"09",
                        "message":"Please wait 1 minute"
                    })
                else:
                    electricityBackend = ElectricityBackend.objects.get(name='Main').active_backend
                    
                    # Buy from 9Payment Backend
                    if electricityBackend == "9Payment":
                        transaction.APIBackend = '9Payment'
                        transaction.save()
                        # Remove temp API KEY
                        APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODA4NjY5OSwianRpIjoiMGNkYjMxY2YtNjNlYy00NDM1LWE3NzQtY2FmMDVkMTAzYjA5IiwiZXhwIjoxNzI4MDkzODk5fQ.z1SAlWhnY8T83XO8RUHf1q_12hhLCTYs_aq73JjqHhaGCSmzq3nYv7DoLcYHGZrboJ4EbOM8Vf29LyD6yc_PmA"
                        # END of remove
                        transaction.APIBackend = '9Payment'
                        transaction.save()
                        url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/pay'
                        
                        payload = {
                            "customerId": meterNumber,
                            "amount": str(amount),
                            "billerId": selectedOperator,
                            "itemId": itemId,
                            "customerPhone": user.phone_number,
                            "customerName": customerName,
                            "otherField": otherField,
                            "debitAccount": "1100000505",
                            "transactionReference": transRef
                            }
                        headers = {
                            'Authorization': f"Bearer {APIKEY}",
                            # 'Content-Type': 'application/json',
                            # 'Accept': 'application/json'
                            }

                        response = requests.request('POST', url, headers=headers, json=payload)
                        responseData = response.json()
                        
                        if responseData['responseCode'] == "200":
                            paymentData = responseData['data']
                            isToken = paymentData['isToken']
                            token = ''
                            #Todo calculate Discount/cashback
                            # airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                            # discountRate = airtimeDiscount.rate
                            # calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                            # Cashback.objects.create(
                            #     user = user,
                            #     transaction_type = 'Airtime',
                            #     message = f"Airtime {transaction.reference}",
                            #     amount = calculatedDiscount
                            # )
                            # wallet.cashback += calculatedDiscount
                            # wallet.save()


                            transaction.status = "Success"
                            transaction.APIBackend = "9Payment"
                            transaction.message = "Transaction successful"
                            transaction.customerName = customerName
                            transaction.customerAddress = otherField #other field is customer address passed from frontend
                            transaction.electricity_units = paymentData['otherField']
                            if isToken == True:
                                transaction.token = paymentData['token']
                                token = paymentData['token']
                            
                            transaction.save()   

                            return JsonResponse({
                                'code':'00',   
                                'isToken':isToken,
                                'token':token,
                                'units':paymentData['otherField'],
                                'reference':transaction.reference,
                                'date':transaction.created, 
                                'backend':"9Payment",                                    
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
                                transaction_type = "Electricity",
                                comment = f"Electricity {transRef} Refund",
                                amount = transaction.amount,
                                balanceBefore = balanceBefore,
                                balanceAfter = wallet.balance,
                            )

                            return JsonResponse({
                                "code":"09",
                                "message":responseData['message']
                            })
                    elif electricityBackend == "SafeHaven":
                        transaction.APIBackend = 'SafeHaven'
                        transaction.save()
                        # Get Access token
                        clientID = settings.SAFEH_CLIENT_ID
                        clientAssertion = settings.SAFEH_CLIENT_ASSERTION
                        utilityAccount = settings.SAFEH_UTILITY_ACCOUNT
                        authToken = ''
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

                            url = "https://api.safehavenmfb.com/vas/pay/utility"                                        
                            headers = {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json',
                                'Authorization':f"Bearer {authToken}",
                                'ClientID':clientID
                            }                            

                            payload = {
                                "amount": float(amount),
                                "channel": "WEB",
                                "serviceCategoryId": selectedOperator,
                                "debitAccountNumber": utilityAccount,
                                "meterNumber": meterNumber,
                                "vendType": meterType.upper()
                                }


                            
                            responseData = requests.request("POST", url, headers=headers, json=payload)
                            
                            responseData = json.loads(responseData.text)
                            print(f"SafeHaven Vend response is '{responseData}' ")
                            if responseData['statusCode'] == 200:
                                details = responseData["data"]
                                metaData = details['metaData']
                                isToken = False
                                token = ''
                                units = '-'

                                transaction.status = "Success"
                                transaction.APIBackend = "SafeHaven"
                                transaction.message = "Transaction successful"
                                transaction.customerName = customerName
                                transaction.customerAddress = otherField #other field is customer address passed from frontend
                                
                                transaction.APIreference = details["reference"]
                                if "token" in metaData :
                                    isToken = True
                                    transaction.token = metaData["token"]
                                    transaction.electricity_units = metaData["units"]
                                    units = metaData["units"]
                                transaction.save()   

                                return JsonResponse({
                                    'code':'00',   
                                    'isToken':isToken,
                                    'token':transaction.token,
                                    'units':units,
                                    'reference':transaction.reference,
                                    'date':transaction.created,   
                                    'backend':"SafeHaven",                               
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
                                    transaction_type = "Electricity",
                                    comment = f"Electricity {transRef} Refund",
                                    amount = transaction.amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )

                                return JsonResponse({
                                    "code":"09",
                                    "message":responseData['message']
                                })
            else:
                return JsonResponse({
                    "code":"09",
                    "message":"Insufficient wallet Balance"
                })

        else:       
            return JsonResponse({
                "code":"09",
                "message":"No funding history found for your account"
            })
        # else:
        #     return JsonResponse({
        #         "code":"01",
        #         "message":"Invalid transaction PIN"
        #     })
    return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })


# Electricity Page 
@login_required(login_url='login')
def cablePage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    # Cable Beneficiary
    cableBeneficiaries = None
    cableDiscount = BillServicesDiscount.objects.get(service_type='Cable').rate
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            cableBeneficiaries = userBeneficiaries.cable
    except ObjectDoesNotExist:
        pass

    cableBackend = CableBackend.objects.get(name='Main').active_backend
    context = {
        'mainBalance':wallet.balance,
        'cableBeneficiaries':cableBeneficiaries,
        'cableBackend':cableBackend,
        'cableDiscount':cableDiscount,
    }
    return render(request,'billpayments/cable.html',context)

# Get Cable Bouquet  
@login_required(login_url='login')
def getCableBouquet(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        selectedOperator = request.GET.get("selectedOperator")
        cableBackend = CableBackend.objects.get(name='Main').active_backend

        cableAvailable = BillPaymentServices.objects.get(service_type="Cable").available

        if cableAvailable:        
            if cableBackend == "9Payment":
                # Remove temp API KEY
                APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyOTM5NzY5NCwianRpIjoiZmFjZGQzNDUtY2Y3Ni00NzQ4LThhYjgtYTBjMDBjMDNmMGMxIiwiZXhwIjoxNzI5NDA0ODk0fQ.Mu2uWC9pSzsATI-ycNdnt1kWSitIOpgCXgfbFF1RvV3t5cv6Ga_TL-l86oXXVbwGn7pnfPlSvixnenEOck4ICQ"
                # END of remove
                url = f'http://102.216.128.75:9090/vas/api/v1/billspayment/fields/{selectedOperator}'
                payload = {
                        }
                headers = {
                        'Authorization': f"Bearer {APIKEY}",
                        # 'Content-Type': 'application/json',
                        # 'Accept': 'application/json'
                        }

                response = requests.request('GET', url, headers=headers,)
                responseDetails = response.json()
                if responseDetails['responseCode'] == '200':
                    operatorData = responseDetails['data']
                    bouquetList = []
                    for entry in operatorData:
                        if entry['fieldName'] == 'itemId':
                            bouquetList = entry['items']
                            break
                    if bouquetList !=[]:
                        return JsonResponse({
                            "code":"00",
                            "bouquetList":bouquetList,
                            'cableBackend':cableBackend,
                        })
                    else:
                        return JsonResponse({
                                "code":"09",
                                "message":"error fetching bouquet, try again later",
                            }) 
                    
                if responseDetails['responseCode'] == '400':
                    return JsonResponse({
                        "code":"09",
                        "message":"Invalid operator"
                    })
            elif cableBackend == "SafeHaven":
                clientID = settings.SAFEH_CLIENT_ID
                clientAssertion = settings.SAFEH_CLIENT_ASSERTION
                authToken = ''
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


                    # VERIFY TRANSACTION
                    url = f"https://api.safehavenmfb.com/vas/service-category/{selectedOperator}/products"                                        
                    headers = {
                        # 'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization':f"Bearer {authToken}",
                        'ClientID':clientID
                    }

                    
                    response = requests.request("GET", url, headers=headers)
                    
                    responseData = json.loads(response.text)
                    if responseData['statusCode'] == 200:

                        return JsonResponse({
                            'code': '00',
                            'bouquetList': responseData['data'],
                            'cableBackend':cableBackend,
                        })
                    else:
                        return JsonResponse({
                                'code': '09',
                                'message': responseData['message'],
                            }) 
        else:
            return JsonResponse({
                'code': '09',
                'message': "cable subscription is currently unavailable",
            })
# Validate smartcard  
@login_required(login_url='login')
def validateSmartcard(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        smartcardNumber = request.GET.get("smartcardNumber")
        selectedOperator = request.GET.get("selectedOperator")
        # meterType = request.GET.get("meterType")
        amount = request.GET.get("amount")
        cableBackend = CableBackend.objects.get(name='Main').active_backend

        
        if cableBackend == "9Payment":
            # Remove temp API KEY
            APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODIwMzI5NCwianRpIjoiYTU1MDAzZDEtNjk4My00ZDExLWJlYzEtZTI3NzQ3ZjhlODZlIiwiZXhwIjoxNzI4MjEwNDk0fQ.PyKt7VuQy5QBt44guG7bTgbQtWnfP_E1dailEyXzGsQvC5nWXQK2bymigmYIPZmfl5bpBHjg_PP-MJv1Cn3BMA"
            # END of remove
            url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/validate'
            payload = {
                    "customerId": smartcardNumber,
                    "amount": str(amount),
                    "billerId": selectedOperator,
                    # "itemId": meterType,
                    }
            headers = {
                    'Authorization': f"Bearer {APIKEY}",
                    # 'Content-Type': 'application/json',
                    # 'Accept': 'application/json'
                    }

            response = requests.request('POST', url, headers=headers, json=payload)
            responseDetails = response.json()
            if responseDetails['responseCode'] == '200':
                customerData = responseDetails['data']
                return JsonResponse({
                    "code":"00",
                    "customerName":customerData['customerName'],
                    "otherField":customerData['otherField'],
                    "amount":customerData['amount'],
                })
            if responseDetails['responseCode'] == '400':
                return JsonResponse({
                    "code":"09",
                    "message":"Invalid meter number"
                })
        elif cableBackend == "SafeHaven":
            clientID = settings.SAFEH_CLIENT_ID
            clientAssertion = settings.SAFEH_CLIENT_ASSERTION
            authToken = ''
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
                # VERIFY METER
                url = "https://api.safehavenmfb.com/vas/verify"                                        
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization':f"Bearer {authToken}",
                    'ClientID':clientID
                }

                
                payload = json.dumps({
                    "serviceCategoryId": selectedOperator,
                    "entityNumber": smartcardNumber
                })
                responseData = requests.request("POST", url, headers=headers, data=payload)
                
                responseData = json.loads(responseData.text)
                if responseData['statusCode'] == 200:
                    customerDetails = responseData['data']
                    return JsonResponse({
                        "code":"00",
                        # "name": customerDetails["name"],
                        "customerName":customerDetails["name"],
                        "otherField":"",
                        "amount":amount,
                        "backend":"SafeHaven",
                    })
                else:
                    return JsonResponse({
                        "code":"09",
                        "message":responseData['message']
                    })

# Ajax call to buy cable
@login_required(login_url='login')
def buyCable(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding
    wallet = UserWallet.objects.get(user=user) 
    lifetimeDiscount = user.discount_genarated
    successfulTransactions = user.successful_transaction_value

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            if (wallet.balance ) > (((totalWalletFunding + (lifetimeDiscount)) - successfulTransactions) + (Decimal(100))):
                user.can_perform_transaction = False
                user.save()
                return JsonResponse({
                    "code":"09",
                    "message":f"internal server error"
                })
            smartcardNumber = request.POST.get("smartcardNumber")
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            packageName = request.POST.get("packageName")
            itemId = request.POST.get("itemId")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            saveBeneficiary = request.POST.get('saveBeneficiary')
            
            # Safe Beneficiary Logic
            if saveBeneficiary == "on":
                try:
                    userBeneficiaries = Beneficiary.objects.get(user=user)
                    if userBeneficiaries is not None:
                        cableBeneficiary = userBeneficiaries.cable 
                        # Search of record already exist
                        alreadySaved = False
                        for entry in cableBeneficiary:
                            # alreadySaved = True
                            if entry['smartcardNumber'] == smartcardNumber:
                                alreadySaved = True
                                break
                        # If rececipient has not been saved before
                        if alreadySaved == False:
                            cableBeneficiary.append(
                                {
                                    "operator":selectedOperatorName,
                                    "smartcardNumber":smartcardNumber,
                                    "customerName":customerName,
                                }
                            ) 
                            userBeneficiaries.cable = cableBeneficiary 
                            userBeneficiaries.save()              
                        
                except ObjectDoesNotExist:
                    newBeneficiary = [{
                        "operator":selectedOperatorName,
                        "smartcardNumber":smartcardNumber,
                        "customerName":customerName,
                        }]
                    # Create Beficiaryobject
                    Beneficiary.objects.create(
                        user = user,
                        cable = newBeneficiary
                    )
            # return JsonResponse({
            #         "code":"09",
            #         "message":"testing electrcity save beneficiary"
            #     })

            # Todo Integrate electricity Services
            # airtimeServices = AirtimeServices.objects.get(network_operator=operator)
            # if airtimeServices.available == False:
            #     return JsonResponse({
            #         "code":"09",
            #         "message":f"{operator} airtime is currently unavailable"
            #     }) 


            # Todo First Check for duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
            if existingTran.count() > 0:
                return JsonResponse({
                    "code":"09",
                    "message":"Please wait 1 minute"
                })
            else:
                cableBackend = CableBackend.objects.get(name='Main').active_backend

                if cableBackend == "9Payment":            
                    # Remove temp API KEY
                    APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODIwMzI5NCwianRpIjoiYTU1MDAzZDEtNjk4My00ZDExLWJlYzEtZTI3NzQ3ZjhlODZlIiwiZXhwIjoxNzI4MjEwNDk0fQ.PyKt7VuQy5QBt44guG7bTgbQtWnfP_E1dailEyXzGsQvC5nWXQK2bymigmYIPZmfl5bpBHjg_PP-MJv1Cn3BMA"
                    # END of remove

                    # Verify selected package price
                    url = f'http://102.216.128.75:9090/vas/api/v1/billspayment/fields/{selectedOperator}'
                    payload = {
                            }
                    headers = {
                            'Authorization': f"Bearer {APIKEY}",
                            # 'Content-Type': 'application/json',
                            # 'Accept': 'application/json'
                            }

                    response = requests.request('GET', url, headers=headers,)
                    responseDetails = response.json()
                    
                    if responseDetails['responseCode'] == '200':
                        operatorData = responseDetails['data']
                        bouquetList = []
                        for entry in operatorData:
                            if entry['fieldName'] == 'itemId':
                                bouquetList = entry['items']
                                break
                        if bouquetList !=[]:
                            packageCost = 0
                            for package in bouquetList:
                                if package['itemId'] == itemId:
                                    packageCost = Decimal(package['amount'])
                                    break
                            
                            if packageCost == amount:
                                # Check if user has enough balance
                                if amount > 0 and amount <= wallet.balance:
                                    cableDiscount = BillServicesDiscount.objects.get(service_type='Cable').rate
                                    calculatedDiscount = Decimal((amount * cableDiscount) / Decimal(100.00))
                                    cableAmount = amount
                                    amount = amount - calculatedDiscount
                                    user.discount_genarated += calculatedDiscount 
                                    balanceBefore = wallet.balance
                                    wallet.balance -= amount
                                    wallet.save()
                                    user.save()
                                    
                                    transRef = reference(25)
                                    try:
                                        existing = Transaction.objects.get(reference=transRef)
                                        while existing is not None:
                                            transRef = reference(25)
                                            existing = Transaction.objects.get(reference=transRef)
                                    except ObjectDoesNotExist:
                                        # Set user referral  codes and create wallet
                                        pass

                                    # Create wallet Activity
                                    WalletActivity.objects.create(
                                        user = user,
                                        event_type = "Debit",
                                        transaction_type = "Cable",
                                        comment = f"Cable {transRef}",
                                        amount = amount,
                                        balanceBefore = balanceBefore,
                                        balanceAfter = wallet.balance,
                                    )
                                    # Create Transaction Record
                                    transaction = Transaction.objects.create(
                                        user = user,
                                        operator = selectedOperatorName,
                                        transaction_type = "Cable",
                                        recipient = smartcardNumber,
                                        reference = transRef,
                                        package = packageName,
                                        amount = amount,
                                        unit_cost = cableAmount,
                                        discount = calculatedDiscount,
                                        balanceBefore = balanceBefore,
                                        balanceAfter = wallet.balance,
                                    )
                        
                                    transaction.refresh_from_db()

                                    user.last_transacted = datetime.now().date()
                                    user.save()

                                    # Second check for duplicate transaction
                                    startTime = datetime.now() - timedelta(seconds=30) 
                                    existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
                                    if existingTran.count() > 1:
                                        return JsonResponse({
                                            "code":"09",
                                            "message":"Please wait 1 minute"
                                        })
                                    else:
                                            
                                        transaction.APIBackend = '9Payment'
                                        transaction.save()
                                        url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/pay'
                                        
                                        payload = {
                                            "customerId": smartcardNumber,
                                            "amount": str(amount),
                                            "billerId": selectedOperator,
                                            "itemId": itemId,
                                            "customerPhone": user.phone_number,
                                            "customerName": customerName,
                                            "otherField": otherField,
                                            "debitAccount": "1100000505",
                                            "transactionReference": transRef
                                            }
                                        headers = {
                                            'Authorization': f"Bearer {APIKEY}",
                                            # 'Content-Type': 'application/json',
                                            # 'Accept': 'application/json'
                                            }

                                        response = requests.request('POST', url, headers=headers, json=payload)
                                        responseData = response.json()
                                        
                                        if responseData['responseCode'] == "200":
                                            paymentData = responseData['data']
                                            isToken = paymentData['isToken']
                                            
                                            

                                            transaction.status = "Success"
                                            transaction.APIBackend = "9Payment"
                                            transaction.message = "Transaction successful"
                                            transaction.customerName = customerName
                                            transaction.customerAddress = otherField #other field is customer address passed from frontend
                                            # transaction.electricity_units = paymentData['otherField']
                                            # if isToken == True:
                                            #     transaction.token = paymentData['token']
                                            #     token = paymentData['token']
                                            
                                            transaction.save()   

                                            return JsonResponse({
                                                'code':'00',   
                                                'isToken':isToken,
                                                'date':transaction.created,                                    
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
                                                transaction_type = "Cable",
                                                comment = f"Cable {transRef} Refund",
                                                amount = transaction.amount,
                                                balanceBefore = balanceBefore,
                                                balanceAfter = wallet.balance,
                                            )

                                            return JsonResponse({
                                                "code":"09",
                                                "message":responseData['message']
                                            })
                                        
                                else:
                                    return JsonResponse({
                                        "code":"09",
                                        "message":"Insufficient wallet Balance"
                                    })
                
                elif cableBackend == "SafeHaven":  
                    # Get Access token
                    clientID = settings.SAFEH_CLIENT_ID
                    clientAssertion = settings.SAFEH_CLIENT_ASSERTION
                    utilityAccount = settings.SAFEH_UTILITY_ACCOUNT
                    authToken = ''
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
                        
                        # VERIFY TRANSACTION
                        url = f"https://api.safehavenmfb.com/vas/service-category/{selectedOperator}/products"                                        
                        headers = {
                            # 'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Authorization':f"Bearer {authToken}",
                            'ClientID':clientID
                        }

                        
                        response = requests.request("GET", url, headers=headers)
                        
                        responseData = json.loads(response.text)
                        if responseData['statusCode'] == 200:
                            bouquets = responseData['data']

                            selectedBouquet = {}

                            for i in range(len(bouquets)):
                                if bouquets[i]["bundleCode"] == itemId:
                                    selectedBouquet = bouquets[i]
                            
                            amount = selectedBouquet["amount"]
                            bouquetName = selectedBouquet["name"]

                            if amount > 0 and amount <= wallet.balance:
                                cableDiscount = BillServicesDiscount.objects.get(service_type='Cable').rate
                                calculatedDiscount = Decimal((amount * cableDiscount) / Decimal(100.00))
                                cableAmount = amount
                                amount = amount - calculatedDiscount
                                user.discount_genarated += calculatedDiscount
                                balanceBefore = wallet.balance
                                wallet.balance -= amount
                                wallet.save()
                                user.save()
                                
                                transRef = reference(25)

                                # discount = Decimal((amount * 0.7) / 100.0)
                                # Create wallet deduction
                                try:
                                    existing = Transaction.objects.get(reference=transRef)
                                    while existing is not None:
                                        transRef = reference(25)
                                        existing = Transaction.objects.get(reference=transRef)
                                except ObjectDoesNotExist:
                                    # Set user referral  codes and create wallet
                                    pass

                                # Create wallet Activity
                                WalletActivity.objects.create(
                                    user = user,
                                    event_type = "Debit",
                                    transaction_type = "Cable",
                                    comment = f"Cable {transRef}",
                                    amount = amount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )
                                # Create Transaction Record
                                transaction = Transaction.objects.create(
                                    user = user,
                                    operator = selectedOperatorName,
                                    transaction_type = "Cable",
                                    recipient = smartcardNumber,
                                    reference = transRef,
                                    package = packageName,
                                    amount = amount,
                                    unit_cost = cableAmount,
                                    discount = calculatedDiscount,
                                    balanceBefore = balanceBefore,
                                    balanceAfter = wallet.balance,
                                )
                    
                                transaction.refresh_from_db()

                                user.last_transacted = datetime.now().date()
                                user.save()

                                # Second check for duplicate transaction
                                startTime = datetime.now() - timedelta(seconds=30) 
                                existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
                                if existingTran.count() > 1:
                                    return JsonResponse({
                                        "code":"09",
                                        "message":"Please wait 1 minute"
                                    })
                                else:                                            
                                    transaction.APIBackend = 'SafeHaven'
                                    transaction.save()



                                    # Make Payment
                                    url = f"https://api.safehavenmfb.com/vas/pay/cable-tv"                                        
                                    headers = {
                                        # 'Content-Type': 'application/json',
                                        'Accept': 'application/json',
                                        'Authorization':f"Bearer {authToken}",
                                        'ClientID':clientID
                                    }

                                    payload = {
                                        "amount": int(amount),
                                        "channel": "WEB",
                                        "serviceCategoryId": selectedOperator,
                                        "debitAccountNumber": utilityAccount,
                                        "bundleCode": itemId,
                                        "cardNumber": smartcardNumber
                                    }                            

                                    
                                    response = requests.request("POST", url, headers=headers, data=payload)
                                    
                                    paymentResponse = json.loads(response.text)
                                    # Successful Transaction
                                    if paymentResponse['statusCode'] == 200:
                                        paymentData = paymentResponse['data']
                                        isToken = False
                                        
                                        #Todo calculate Discount/cashback
                                        # airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                                        # discountRate = airtimeDiscount.rate
                                        # calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                                        # Cashback.objects.create(
                                        #     user = user,
                                        #     transaction_type = 'Airtime',
                                        #     message = f"Airtime {transaction.reference}",
                                        #     amount = calculatedDiscount
                                        # )
                                        # wallet.cashback += calculatedDiscount
                                        # wallet.save()


                                        transaction.status = "Success"
                                        transaction.APIBackend = "SafeHaven"
                                        transaction.APIreference = paymentData["reference"]
                                        # transaction.discount = calculatedDiscount
                                        transaction.message = "Transaction successful"
                                        transaction.customerName = customerName
                                        
                                        transaction.customerAddress = '-' #other field is customer address passed from frontend
                                        # transaction.electricity_units = paymentData['otherField']
                                        # if isToken == True:
                                        #     transaction.token = paymentData['token']
                                        #     token = paymentData['token']
                                        
                                        transaction.save()   

                                        return JsonResponse({
                                            'code':'00',   
                                            'isToken':isToken,
                                            'date':transaction.created,                                    
                                        })

                                        
                                    # Failed Transaction
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
                                            transaction_type = "Cable",
                                            comment = f"Cable {transRef} Refund",
                                            amount = transaction.amount,
                                            balanceBefore = balanceBefore,
                                            balanceAfter = wallet.balance,
                                        )

                                        return JsonResponse({
                                            "code":"09",
                                            "message":paymentResponse['message']
                                        })

                            else:
                                user.transacting = False
                                user.save()
                                return JsonResponse({
                                    'code':'09',
                                    'message':"Insufficient wallet Balance"
                                    }) 
                        else:
                            return JsonResponse({
                                "code":"09",
                                "message":responseData['message']
                            })
                    else:
                        return JsonResponse({
                            "code":"09",
                            "message":"authentication error"
                        })
                    
        else:       
            return JsonResponse({
                "code":"09",
                "message":"No funding history found for your account"
            })
        # else:
        #     return JsonResponse({
        #         "code":"01",
        #         "message":"Invalid transaction PIN"
        #     })
    return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })


# Bet funding Page 
@login_required(login_url='login')
def betFundingPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    # Telecomms Beneficiary
    betFundingBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            betFundingBeneficiaries = userBeneficiaries.bet_funding
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'betFundingBeneficiaries':betFundingBeneficiaries
    }
    return render(request,'billpayments/bet-funding.html',context)

# Validate betting ID  
@login_required(login_url='login')
def validateBettingAccount(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        accountId = request.GET.get("accountId")
        selectedOperator = request.GET.get("selectedOperator")
        # meterType = request.GET.get("meterType")
        amount = request.GET.get("amount")

        # API CALL to validate meter

        # Remove temp API KEY
        APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyOTA4NTYzMiwianRpIjoiMDNlMTMyYWYtMmY3Yy00ZmM5LWEzOWEtNTZjNjc1YmRiZjI1IiwiZXhwIjoxNzI5MDkyODMyfQ.7Kb9tCpxg5LLWodGztpSi2qRgEL0NQLcfOsW6JnV0PhGGLpSndaWNj7dbA47q6qyFfishhw04M6-pGEHqnBzKQ"
        # END of remove
        url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/validate'
        payload = {
                "customerId": accountId,
                "amount": str(amount),
                "billerId": selectedOperator,
                # "itemId": meterType,
                }
        headers = {
                'Authorization': f"Bearer {APIKEY}",
                # 'Content-Type': 'application/json',
                # 'Accept': 'application/json'
                }

        response = requests.request('POST', url, headers=headers, json=payload)
        responseDetails = response.json()
        if responseDetails['responseCode'] == '200':
            customerData = responseDetails['data']
            return JsonResponse({
                "code":"00",
                "customerName":customerData['customerName'],
                "otherField":customerData['otherField'],
                "amount":customerData['amount'],
            })
        if responseDetails['responseCode'] == '400':
            return JsonResponse({
                "code":"09",
                "message":"Invalid betting account"
            })


# Ajax call to buy cable
@login_required(login_url='login')
def fundBettingWallet(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            accountId = request.POST.get("accountId")
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            saveBeneficiary = request.POST.get('saveBeneficiary')
            
            # Get user wallet
            wallet = UserWallet.objects.get(user=user)

            # Safe Beneficiary Logic
            if saveBeneficiary == "on":
                try:
                    userBeneficiaries = Beneficiary.objects.get(user=user)
                    if userBeneficiaries is not None:
                        betFundingBeneficiary = userBeneficiaries.bet_funding 
                        # Search of record already exist
                        alreadySaved = False
                        for entry in betFundingBeneficiary:
                            # alreadySaved = True
                            if entry['accountId'] == accountId:
                                alreadySaved = True
                                break
                        # If rececipient has not been saved before
                        if alreadySaved == False:
                            betFundingBeneficiary.append(
                                {
                                    "operator":selectedOperatorName,
                                    "accountId":accountId,
                                    "customerName":customerName,
                                }
                            ) 
                            userBeneficiaries.bet_funding = betFundingBeneficiary 
                            userBeneficiaries.save() 
                        
                except ObjectDoesNotExist:
                    newBeneficiary = [{
                        "operator":selectedOperatorName,
                        "accountId":accountId,
                        "customerName":customerName,
                        }]
                    # Create Beficiaryobject
                    Beneficiary.objects.create(
                        user = user,
                        bet_funding = newBeneficiary
                    )

            # Todo Integrate electricity Services
            # airtimeServices = AirtimeServices.objects.get(network_operator=operator)
            # if airtimeServices.available == False:
            #     return JsonResponse({
            #         "code":"09",
            #         "message":f"{operator} airtime is currently unavailable"
            #     }) 


            # Todo First Check for duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
            if existingTran.count() > 0:
                return JsonResponse({
                    "code":"09",
                    "message":"Please wait 1 minute"
                })
            
            # Remove temp API KEY
            APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyOTA4NDk5MCwianRpIjoiMDM5NDhkZGUtN2QxOC00ZWE2LThlNzAtYWQ2MDU1MmE0MmEyIiwiZXhwIjoxNzI5MDkyMTkwfQ.j1wMy8mmPYx15ilvDha6Q0YICElY5LRzOSWQz3ou1ZM3pj_JbyJqOZNnTOemJGR8BeDJiSac7dqbjiKiZPtMGA"
            # END of remove

            
            if amount > 0 and amount <= wallet.balance:
                balanceBefore = wallet.balance
                wallet.balance -= amount
                wallet.save()
                
                transRef = reference(25)
                try:
                    existing = Transaction.objects.get(reference=transRef)
                    while existing is not None:
                        transRef = reference(25)
                        existing = Transaction.objects.get(reference=transRef)
                except ObjectDoesNotExist:
                    # Set user referral  codes and create wallet
                    pass

                # Create wallet Activity
                WalletActivity.objects.create(
                    user = user,
                    event_type = "Debit",
                    transaction_type = "Bet Funding",
                    comment = f"Bet Funding {transRef}",
                    amount = Decimal(amount),
                    balanceBefore = balanceBefore,
                    balanceAfter = wallet.balance,
                )
                # Create Transaction Record
                transaction = Transaction.objects.create(
                    user = user,
                    operator = selectedOperatorName,
                    transaction_type = "Bet Funding",
                    recipient = accountId,
                    reference = transRef,
                    amount = amount,
                    balanceBefore = balanceBefore,
                    balanceAfter = wallet.balance,
                )

                transaction.refresh_from_db()

                user.last_transacted = datetime.now().date()
                user.save()

                # Second check for duplicate transaction
                startTime = datetime.now() - timedelta(seconds=30) 
                existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
                if existingTran.count() > 1:
                    return JsonResponse({
                        "code":"09",
                        "message":"Please wait 1 minute"
                    })
                else:
                    bettingBackend = CableBackend.objects.get(name='Main')
                    
                    # Buy from 9Payment Backend
                    if bettingBackend.active_backend == "9Payment":
                        
                        transaction.APIBackend = '9Payment'
                        transaction.save()
                        url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/pay'
                        
                        payload = {
                            "customerId": accountId,
                            "amount": str(amount),
                            # "billerId": selectedOperator,
                            "billerId": "BETKING",
                            # "itemId": itemId,
                            "customerPhone": user.phone_number,
                            "customerName": customerName,
                            "otherField": otherField,
                            "debitAccount": "1100000505",
                            "transactionReference": transRef
                            }
                        headers = {
                            'Authorization': f"Bearer {APIKEY}",
                            # 'Content-Type': 'application/json',
                            # 'Accept': 'application/json'
                            }

                        response = requests.request('POST', url, headers=headers, json=payload)
                        responseData = response.json()
                        
                        if responseData['responseCode'] == "200":
                            paymentData = responseData['data']
                            isToken = paymentData['isToken']
                            
                            #Todo calculate Discount/cashback
                            # airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                            # discountRate = airtimeDiscount.rate
                            # calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                            # Cashback.objects.create(
                            #     user = user,
                            #     transaction_type = 'Airtime',
                            #     message = f"Airtime {transaction.reference}",
                            #     amount = calculatedDiscount
                            # )
                            # wallet.cashback += calculatedDiscount
                            # wallet.save()


                            transaction.status = "Success"
                            transaction.APIBackend = "9Payment"
                            # transaction.discount = calculatedDiscount
                            transaction.message = "Transaction successful"
                            transaction.customerName = customerName
                            transaction.customerAddress = otherField #other field is customer address passed from frontend
                            # transaction.electricity_units = paymentData['otherField']
                            # if isToken == True:
                            #     transaction.token = paymentData['token']
                            #     token = paymentData['token']
                            
                            transaction.save()   

                            return JsonResponse({
                                'code':'00',   
                                'isToken':isToken,
                                'date':transaction.created,                                    
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
                                transaction_type = "Bet Funding",
                                comment = f"Bet Funding {transRef} Refund",
                                amount = transaction.amount,
                                balanceBefore = balanceBefore,
                                balanceAfter = wallet.balance,
                            )

                            return JsonResponse({
                                "code":"09",
                                "message":responseData['message']
                            })
                    
            else:
                return JsonResponse({
                    "code":"09",
                    "message":"Insufficient wallet Balance"
                })

        else:       
            return JsonResponse({
                "code":"09",
                "message":"No funding history found for your account"
            })
        # else:
        #     return JsonResponse({
        #         "code":"01",
        #         "message":"Invalid transaction PIN"
        #     })
    return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })


# Electricity Page 
@login_required(login_url='login')
def internetPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    # Telecomms Beneficiary
    internetBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            internetBeneficiaries = userBeneficiaries.internet
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'internetBeneficiaries':internetBeneficiaries,
    }
    return render(request,'billpayments/internet.html',context)

# Get ISP Plans  
@login_required(login_url='login')
def getInternetPlans(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        selectedOperator = request.GET.get("selectedOperator")

        # API CALL to validate meter

        # Remove temp API KEY
        APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODk5MjcxMywianRpIjoiN2QwZmQ0MjEtNDFhNS00ZTc1LWI5ODctMWE3ZjhlYTZkMGE3IiwiZXhwIjoxNzI4OTk5OTEzfQ.4t_v2ZxZey1S49sx7-sosONnatMg0MX8XIUS0g7TtHiUh6MbK_YX6hGowjJ1I3rNLoezzuZWxBus7c7I7vS7Pg"
        # END of remove
        url = f'http://102.216.128.75:9090/vas/api/v1/billspayment/fields/{selectedOperator}'
        payload = {
                }
        headers = {
                'Authorization': f"Bearer {APIKEY}",
                # 'Content-Type': 'application/json',
                # 'Accept': 'application/json'
                }
        

        response = requests.request('GET', url, headers=headers,)
        responseDetails = response.json()
        if responseDetails['responseCode'] == '200':
            operatorData = responseDetails['data']
            bouquetList = []
            for entry in operatorData:
                if entry['fieldName'] == 'itemId':
                    bouquetList = entry['items']
                    break
            if bouquetList !=[]:
                return JsonResponse({
                    "code":"00",
                    "bouquetList":bouquetList,
                })
            else:
               return JsonResponse({
                    "code":"09",
                    "message":"error fetching bouquet, try again later",
                }) 
            
        if responseDetails['responseCode'] == '400':
            return JsonResponse({
                "code":"09",
                "message":"Invalid operator"
            })


# Validate ISP Customer  
@login_required(login_url='login')
def validateInternetCustomer(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        customerID = request.GET.get("customerID")
        selectedOperator = request.GET.get("selectedOperator")
        # meterType = request.GET.get("meterType")
        amount = request.GET.get("amount")

        # API CALL to validate meter

        # Remove temp API KEY
        APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODk5MjcxMywianRpIjoiN2QwZmQ0MjEtNDFhNS00ZTc1LWI5ODctMWE3ZjhlYTZkMGE3IiwiZXhwIjoxNzI4OTk5OTEzfQ.4t_v2ZxZey1S49sx7-sosONnatMg0MX8XIUS0g7TtHiUh6MbK_YX6hGowjJ1I3rNLoezzuZWxBus7c7I7vS7Pg"
        # END of remove
        url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/validate'
        payload = {
                "customerId": customerID,
                "amount": str(amount),
                "billerId": selectedOperator,
                # "itemId": meterType,
                }
        headers = {
                'Authorization': f"Bearer {APIKEY}",
                # 'Content-Type': 'application/json',
                # 'Accept': 'application/json'
                }

        response = requests.request('POST', url, headers=headers, json=payload)
        responseDetails = response.json()
        if responseDetails['responseCode'] == '200':
            customerData = responseDetails['data']
            return JsonResponse({
                "code":"00",
                "customerName":customerData['customerName'],
                "otherField":customerData['otherField'],
                "amount":customerData['amount'],
            })
        if responseDetails['responseCode'] == '400':
            return JsonResponse({
                "code":"09",
                "message":"Invalid customer ID"
            })
        
# Ajax call to buy internet plan
@login_required(login_url='login')
def buyInternetPlan(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            customerID = request.POST.get("customerID")
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            packageName = request.POST.get("packageName")
            itemId = request.POST.get("itemId")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            saveBeneficiary = request.POST.get('saveBeneficiary')
            
            # Get user wallet
            wallet = UserWallet.objects.get(user=user)

            # Safe Beneficiary Logic
            if saveBeneficiary == "on":
                try:
                    userBeneficiaries = Beneficiary.objects.get(user=user)
                    if userBeneficiaries is not None:
                        internetBeneficiary = userBeneficiaries.internet 
                        # Search of record already exist
                        alreadySaved = False
                        for entry in internetBeneficiary:
                            # alreadySaved = True
                            if entry['customerID'] == customerID:
                                alreadySaved = True
                                break
                        # If rececipient has not been saved before
                        if alreadySaved == False:
                            internetBeneficiary.append(
                                {
                                    "operator":selectedOperatorName,
                                    "customerID":customerID,
                                    "customerName":customerName,
                                }
                            ) 
                            userBeneficiaries.internet = internetBeneficiary 
                            userBeneficiaries.save() 
                        
                except ObjectDoesNotExist:
                    newBeneficiary = [{
                        "operator":selectedOperatorName,
                        "customerID":customerID,
                        "customerName":customerName,
                        }]
                    # Create Beficiaryobject
                    Beneficiary.objects.create(
                        user = user,
                        internet = newBeneficiary
                    )

            # Todo Integrate electricity Services
            # airtimeServices = AirtimeServices.objects.get(network_operator=operator)
            # if airtimeServices.available == False:
            #     return JsonResponse({
            #         "code":"09",
            #         "message":f"{operator} airtime is currently unavailable"
            #     }) 


            # Todo First Check for duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
            if existingTran.count() > 0:
                return JsonResponse({
                    "code":"09",
                    "message":"Please wait 1 minute"
                })
            
            # Remove temp API KEY
            APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODk5MjcxMywianRpIjoiN2QwZmQ0MjEtNDFhNS00ZTc1LWI5ODctMWE3ZjhlYTZkMGE3IiwiZXhwIjoxNzI4OTk5OTEzfQ.4t_v2ZxZey1S49sx7-sosONnatMg0MX8XIUS0g7TtHiUh6MbK_YX6hGowjJ1I3rNLoezzuZWxBus7c7I7vS7Pg"
            # END of remove

            # Verify selected package price
            url = f'http://102.216.128.75:9090/vas/api/v1/billspayment/fields/{selectedOperator}'
            payload = {
                    }
            headers = {
                    'Authorization': f"Bearer {APIKEY}",
                    # 'Content-Type': 'application/json',
                    # 'Accept': 'application/json'
                    }

            response = requests.request('GET', url, headers=headers,)
            responseDetails = response.json()
            
            if responseDetails['responseCode'] == '200':
                operatorData = responseDetails['data']
                bouquetList = []
                for entry in operatorData:
                    if entry['fieldName'] == 'itemId':
                        bouquetList = entry['items']
                        break
                if bouquetList !=[]:
                    packageCost = 0
                    for package in bouquetList:
                        if package['itemId'] == itemId:
                            packageCost = Decimal(package['amount'])
                            break
                    
                    if packageCost == amount:
                        # Check if user has enough balance
                        if amount > 0 and amount <= wallet.balance:
                            balanceBefore = wallet.balance
                            wallet.balance -= amount
                            wallet.save()
                            
                            transRef = reference(25)
                            try:
                                existing = Transaction.objects.get(reference=transRef)
                                while existing is not None:
                                    transRef = reference(25)
                                    existing = Transaction.objects.get(reference=transRef)
                            except ObjectDoesNotExist:
                                # Set user referral  codes and create wallet
                                pass

                            # Create wallet Activity
                            WalletActivity.objects.create(
                                user = user,
                                event_type = "Debit",
                                transaction_type = "Internet",
                                comment = f"Internet {transRef}",
                                amount = Decimal(amount),
                                balanceBefore = balanceBefore,
                                balanceAfter = wallet.balance,
                            )
                            # Create Transaction Record
                            transaction = Transaction.objects.create(
                                user = user,
                                operator = selectedOperatorName,
                                transaction_type = "Internet",
                                recipient = customerID,
                                reference = transRef,
                                package = packageName,
                                amount = amount,
                                balanceBefore = balanceBefore,
                                balanceAfter = wallet.balance,
                            )
                
                            transaction.refresh_from_db()

                            user.last_transacted = datetime.now().date()
                            user.save()

                            # Second check for duplicate transaction
                            startTime = datetime.now() - timedelta(seconds=30) 
                            existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
                            if existingTran.count() > 1:
                                return JsonResponse({
                                    "code":"09",
                                    "message":"Please wait 1 minute"
                                })
                            else:
                                cableBackend = CableBackend.objects.get(name='Main')
                                
                                # Buy from 9Payment Backend
                                if cableBackend.active_backend == "9Payment":
                                    
                                    transaction.APIBackend = '9Payment'
                                    transaction.save()
                                    url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/pay'
                                    
                                    payload = {
                                        "customerId": customerID,
                                        "amount": str(amount),
                                        "billerId": selectedOperator,
                                        "itemId": itemId,
                                        # "customerPhone": user.phone_number,
                                        "customerName": customerName,
                                        # "otherField": otherField,
                                        "debitAccount": "1100000505",
                                        "transactionReference": transRef
                                        }
                                    headers = {
                                        'Authorization': f"Bearer {APIKEY}",
                                        # 'Content-Type': 'application/json',
                                        # 'Accept': 'application/json'
                                        }

                                    response = requests.request('POST', url, headers=headers, json=payload)
                                    responseData = response.json()
                                    
                                    if responseData['responseCode'] == "200":
                                        paymentData = responseData['data']
                                        isToken = paymentData['isToken']
                                        
                                        #Todo calculate Discount/cashback
                                        # airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                                        # discountRate = airtimeDiscount.rate
                                        # calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                                        # Cashback.objects.create(
                                        #     user = user,
                                        #     transaction_type = 'Airtime',
                                        #     message = f"Airtime {transaction.reference}",
                                        #     amount = calculatedDiscount
                                        # )
                                        # wallet.cashback += calculatedDiscount
                                        # wallet.save()


                                        transaction.status = "Success"
                                        transaction.APIBackend = "9Payment"
                                        # transaction.discount = calculatedDiscount
                                        transaction.message = "Transaction successful"
                                        transaction.customerName = customerName
                                        transaction.customerAddress = otherField #other field is customer address passed from frontend
                                        # transaction.electricity_units = paymentData['otherField']
                                        # if isToken == True:
                                        #     transaction.token = paymentData['token']
                                        #     token = paymentData['token']
                                        
                                        transaction.save()   

                                        return JsonResponse({
                                            'code':'00',   
                                            'isToken':isToken,
                                            'date':transaction.created,                                    
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
                                            transaction_type = "Internet",
                                            comment = f"Internet {transRef} Refund",
                                            amount = transaction.amount,
                                            balanceBefore = balanceBefore,
                                            balanceAfter = wallet.balance,
                                        )

                                        return JsonResponse({
                                            "code":"09",
                                            "message":responseData['message']
                                        })
                                
                        else:
                            return JsonResponse({
                                "code":"09",
                                "message":"Insufficient wallet Balance"
                            })

        else:       
            return JsonResponse({
                "code":"09",
                "message":"No funding history found for your account"
            })
        # else:
        #     return JsonResponse({
        #         "code":"01",
        #         "message":"Invalid transaction PIN"
        #     })
    return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })


# Education PIN 
@login_required(login_url='login')
def educationPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    # Telecomms Beneficiary
    educationBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            educationBeneficiaries = userBeneficiaries.education
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'educationBeneficiaries':educationBeneficiaries,
    }
    return render(request,'billpayments/education.html',context)

# Get ISP Plans  
@login_required(login_url='login')
def getEducationData(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        selectedOperator = request.GET.get("selectedOperator")

        # API CALL to validate meter

        # Remove temp API KEY
        APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyOTA4MTg2NCwianRpIjoiY2U2MDc5NjktNzNiNC00ZDMxLTgwYTUtYTQ2MzRkODQ2MTYwIiwiZXhwIjoxNzI5MDg5MDY0fQ.h3cPQ69hHPXsMA3fnr2TaTm7mIL8lvTaoA3ZyR0_Et0YKll-x-yLL35agRpGCV4-ifwjg36dJ0SWamZSb2oNDw"
        # END of remove
        url = f'http://102.216.128.75:9090/vas/api/v1/billspayment/fields/{selectedOperator}'
        payload = {
                }
        headers = {
                'Authorization': f"Bearer {APIKEY}",
                # 'Content-Type': 'application/json',
                # 'Accept': 'application/json'
                }
        

        response = requests.request('GET', url, headers=headers,)
        responseDetails = response.json()
        if responseDetails['responseCode'] == '200':
            operatorData = responseDetails['data']
            bouquetList = []
            for entry in operatorData:
                if entry['fieldName'] == 'itemId':
                    bouquetList = entry['items']
                    break
            if bouquetList !=[]:
                return JsonResponse({
                    "code":"00",
                    "bouquetList":bouquetList,
                })
            else:
               return JsonResponse({
                    "code":"09",
                    "message":"error fetching bouquet, try again later",
                }) 
            
        if responseDetails['responseCode'] == '400':
            return JsonResponse({
                "code":"09",
                "message":"Invalid operator"
            })


# Ajax call to buy EPIN plan
@login_required(login_url='login')
def buyEducationPIN(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            packageName = request.POST.get("packageName")
            itemId = request.POST.get("itemId")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            customerID = user.phone_number
            email = user.email
            
            # Get user wallet
            wallet = UserWallet.objects.get(user=user)

            # Safe Beneficiary Logic
            
            # Todo Integrate electricity Services
            # airtimeServices = AirtimeServices.objects.get(network_operator=operator)
            # if airtimeServices.available == False:
            #     return JsonResponse({
            #         "code":"09",
            #         "message":f"{operator} airtime is currently unavailable"
            #     }) 


            # Todo First Check for duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
            if existingTran.count() > 0:
                return JsonResponse({
                    "code":"09",
                    "message":"Please wait 1 minute"
                })
            
            # Remove temp API KEY
            APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyOTA4MTg2NCwianRpIjoiY2U2MDc5NjktNzNiNC00ZDMxLTgwYTUtYTQ2MzRkODQ2MTYwIiwiZXhwIjoxNzI5MDg5MDY0fQ.h3cPQ69hHPXsMA3fnr2TaTm7mIL8lvTaoA3ZyR0_Et0YKll-x-yLL35agRpGCV4-ifwjg36dJ0SWamZSb2oNDw"
            # END of remove

            # Verify selected package price
            url = f'http://102.216.128.75:9090/vas/api/v1/billspayment/fields/{selectedOperator}'
            payload = {
                    }
            headers = {
                    'Authorization': f"Bearer {APIKEY}",
                    # 'Content-Type': 'application/json',
                    # 'Accept': 'application/json'
                    }

            response = requests.request('GET', url, headers=headers,)
            responseDetails = response.json()
            
            if responseDetails['responseCode'] == '200':
                operatorData = responseDetails['data']
                bouquetList = []
                for entry in operatorData:
                    if entry['fieldName'] == 'itemId':
                        bouquetList = entry['items']
                        break
                if bouquetList !=[]:
                    packageCost = 0
                    for package in bouquetList:
                        if package['itemId'] == itemId:
                            packageCost = Decimal(package['amount'])
                            break
                    
                    if packageCost == amount:
                        # Check if user has enough balance
                        if amount > 0 and amount <= wallet.balance:
                            balanceBefore = wallet.balance
                            wallet.balance -= amount
                            wallet.save()
                            
                            transRef = reference(25)
                            try:
                                existing = Transaction.objects.get(reference=transRef)
                                while existing is not None:
                                    transRef = reference(25)
                                    existing = Transaction.objects.get(reference=transRef)
                            except ObjectDoesNotExist:
                                # Set user referral  codes and create wallet
                                pass

                            # Create wallet Activity
                            WalletActivity.objects.create(
                                user = user,
                                event_type = "Debit",
                                transaction_type = "Education",
                                comment = f"Education {transRef}",
                                amount = Decimal(amount),
                                balanceBefore = balanceBefore,
                                balanceAfter = wallet.balance,
                            )
                            # Create Transaction Record
                            transaction = Transaction.objects.create(
                                user = user,
                                operator = selectedOperatorName,
                                transaction_type = "Education",
                                recipient = customerID,
                                reference = transRef,
                                package = packageName,
                                amount = amount,
                                balanceBefore = balanceBefore,
                                balanceAfter = wallet.balance,
                            )
                
                            transaction.refresh_from_db()

                            user.last_transacted = datetime.now().date()
                            user.save()

                            # Second check for duplicate transaction
                            startTime = datetime.now() - timedelta(seconds=30) 
                            existingTran = Transaction.objects.filter(user=user,created__gte=datetime.now() - timedelta(seconds=45))
                            if existingTran.count() > 1:
                                return JsonResponse({
                                    "code":"09",
                                    "message":"Please wait 1 minute"
                                })
                            else:
                                epinBackend = EPINBackend.objects.get(name='Main')
                                
                                # Buy from 9Payment Backend
                                if epinBackend.active_backend == "9Payment":
                                    
                                    transaction.APIBackend = '9Payment'
                                    transaction.save()
                                    url = 'http://102.216.128.75:9090/vas/api/v1/billspayment/pay'
                                    
                                    payload = {
                                        "customerId": customerID,
                                        "amount": str(amount),
                                        "billerId": selectedOperator,
                                        "itemId": itemId,
                                        "customerPhone": user.phone_number,
                                        "customerName": customerName,
                                        "otherField": email,
                                        "debitAccount": "1100000505",
                                        "transactionReference": transRef
                                        }
                                    headers = {
                                        'Authorization': f"Bearer {APIKEY}",
                                        # 'Content-Type': 'application/json',
                                        # 'Accept': 'application/json'
                                        }

                                    response = requests.request('POST', url, headers=headers, json=payload)
                                    responseData = response.json()
                                    
                                    if responseData['responseCode'] == "200":
                                        paymentData = responseData['data']
                                        isToken = paymentData['isToken']
                                        
                                        #Todo calculate Discount/cashback
                                        # airtimeDiscount = AirtimeDiscount.objects.get(networkOperator=operator)
                                        # discountRate = airtimeDiscount.rate
                                        # calculatedDiscount = Decimal((transaction.amount * discountRate) / Decimal(100))
                                        # Cashback.objects.create(
                                        #     user = user,
                                        #     transaction_type = 'Airtime',
                                        #     message = f"Airtime {transaction.reference}",
                                        #     amount = calculatedDiscount
                                        # )
                                        # wallet.cashback += calculatedDiscount
                                        # wallet.save()


                                        transaction.status = "Success"
                                        transaction.APIBackend = "9Payment"
                                        # transaction.discount = calculatedDiscount
                                        transaction.message = "Transaction successful"
                                        transaction.customerName = customerName
                                        transaction.education_data = paymentData
                                        # if isToken == True:
                                        #     transaction.token = paymentData['token']
                                        #     token = paymentData['token']
                                        
                                        transaction.save()   

                                        return JsonResponse({
                                            'code':'00',   
                                            'isToken':isToken,
                                            'date':transaction.created,  
                                            'data':paymentData                                 
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
                                            transaction_type = "Education",
                                            comment = f"Education {transRef} Refund",
                                            amount = transaction.amount,
                                            balanceBefore = balanceBefore,
                                            balanceAfter = wallet.balance,
                                        )

                                        return JsonResponse({
                                            "code":"09",
                                            "message":responseData['message']
                                        })
                                
                        else:
                            return JsonResponse({
                                "code":"09",
                                "message":"Insufficient wallet Balance"
                            })

        else:       
            return JsonResponse({
                "code":"09",
                "message":"No funding history found for your account"
            })
        # else:
        #     return JsonResponse({
        #         "code":"01",
        #         "message":"Invalid transaction PIN"
        #     })
    return JsonResponse({
                "code":"09",
                "message":"Invalid request"
            })
