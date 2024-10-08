from django.shortcuts import render
from decimal import Decimal
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from django.core.exceptions import ObjectDoesNotExist

from adminbackend.models import CableBackend, ElectricityBackend
from users.models import Beneficiary, Transaction, UserWallet, WalletActivity
from vuvu.custom_functions import is_ajax, reference

from datetime import datetime, timedelta


# Electricity Page 
@login_required(login_url='login')
def electricityPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    # Telecomms Beneficiary
    electricityBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            electricityBeneficiaries = userBeneficiaries.electricity
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'electricityBeneficiaries':electricityBeneficiaries
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
        print(responseDetails)
        if responseDetails['responseCode'] == '200':
            customerData = responseDetails['data']
            return JsonResponse({
                "code":"00",
                "customerName":customerData['customerName'],
                "address":customerData['otherField'],
                "amount":customerData['amount'],
            })
        if responseDetails['responseCode'] == '400':
            return JsonResponse({
                "code":"09",
                "message":"Invalid meter number"
            })


# Ajax call to buy Electricity
@login_required(login_url='login')
def buyElectricity(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            print(request.POST)
            meterNumber = request.POST.get("meterNumber")
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            meterType = request.POST.get("meterType")
            itemId = request.POST.get("itemId")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            print(f"sent amount is {amount}")
            saveBeneficiary = request.POST.get('saveBeneficiary')
            
            # Get user wallet
            wallet = UserWallet.objects.get(user=user)

            # Safe Beneficiary Logic
            if saveBeneficiary == "on":
                try:
                    userBeneficiaries = Beneficiary.objects.get(user=user)
                    if userBeneficiaries is not None:
                        electricityBeneficiary = userBeneficiaries.electricity 
                        # Search of record already exist
                        alreadySaved = False
                        for entry in electricityBeneficiary:
                            # print(entry)
                            # alreadySaved = True
                            if entry['meterNumber'] == meterNumber:
                                alreadySaved = True
                                print("Record already saved")
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
                            userBeneficiaries.telecomms = electricityBeneficiary 
                            userBeneficiaries.save() 
                            print("New beneficary added")               
                        print(f"these are the current telecomms beneficiaries 2 {electricityBeneficiary}")
                        
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
                        telecomms = newBeneficiary
                    )

            # Todo Integrate electricity Services
            # airtimeServices = AirtimeServices.objects.get(network_operator=operator)
            # if airtimeServices.available == False:
            #     return JsonResponse({
            #         "code":"09",
            #         "message":f"{operator} airtime is currently unavailable"
            #     }) 


            # Todo First Check for duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,operator=selectedOperatorName,recipient=meterNumber,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
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
                    amount = Decimal(amount),
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
                    balanceBefore = balanceBefore,
                    balanceAfter = wallet.balance,
                )
    
                transaction.refresh_from_db()

                user.last_transacted = datetime.now().date()
                user.save()

                # Second check for duplicate transaction
                startTime = datetime.now() - timedelta(seconds=30) 
                existingTran = Transaction.objects.filter(user=user,operator=selectedOperatorName,recipient=meterNumber,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
                if existingTran.count() > 1:
                    return JsonResponse({
                        "code":"09",
                        "message":"Duplicate transaction wait 1 minute"
                    })
                else:
                    electricityBackend = ElectricityBackend.objects.get(name='Main')
                    
                    # Buy from 9Payment Backend
                    if electricityBackend.active_backend == "9Payment":
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
                        print(f"9Payment response is {responseData}")
                        
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
                            # transaction.discount = calculatedDiscount
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
    # Telecomms Beneficiary
    cableBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            cableBeneficiaries = userBeneficiaries.cable
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'cableBeneficiaries':cableBeneficiaries
    }
    return render(request,'billpayments/cable.html',context)

# Get Cable Bouquet  
@login_required(login_url='login')
def getCableBouquet(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        selectedOperator = request.GET.get("selectedOperator")

        # API CALL to validate meter

        # Remove temp API KEY
        APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODIwMzI5NCwianRpIjoiYTU1MDAzZDEtNjk4My00ZDExLWJlYzEtZTI3NzQ3ZjhlODZlIiwiZXhwIjoxNzI4MjEwNDk0fQ.PyKt7VuQy5QBt44guG7bTgbQtWnfP_E1dailEyXzGsQvC5nWXQK2bymigmYIPZmfl5bpBHjg_PP-MJv1Cn3BMA"
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
        # print(responseDetails)
        if responseDetails['responseCode'] == '200':
            operatorData = responseDetails['data']
            bouquetList = []
            for entry in operatorData:
                if entry['fieldName'] == 'itemId':
                    bouquetList = entry['items']
                    break
            # print(f"bouquet list is {bouqueList}")
            if bouquetList !=[]:
                print(f"bouquet list is {bouquetList}")
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

# Validate smartcard  
@login_required(login_url='login')
def validateSmartcard(request):
    user = request.user
    if is_ajax(request) and request.method == "GET":
        smartcardNumber = request.GET.get("smartcardNumber")
        selectedOperator = request.GET.get("selectedOperator")
        # meterType = request.GET.get("meterType")
        amount = request.GET.get("amount")

        # API CALL to validate meter

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
        print(responseDetails)
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


# Ajax call to buy cable
@login_required(login_url='login')
def buyCable(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST": 
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            print(request.POST)
            smartcardNumber = request.POST.get("smartcardNumber")
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            packageName = request.POST.get("packageName")
            itemId = request.POST.get("itemId")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            print(f"sent amount is {amount}")
            saveBeneficiary = request.POST.get('saveBeneficiary')
            
            # Get user wallet
            wallet = UserWallet.objects.get(user=user)

            # Safe Beneficiary Logic
            if saveBeneficiary == "on":
                try:
                    userBeneficiaries = Beneficiary.objects.get(user=user)
                    if userBeneficiaries is not None:
                        electricityBeneficiary = userBeneficiaries.electricity 
                        # Search of record already exist
                        alreadySaved = False
                        for entry in electricityBeneficiary:
                            # print(entry)
                            # alreadySaved = True
                            if entry['smartcardNumber'] == smartcardNumber:
                                alreadySaved = True
                                print("Record already saved")
                                break
                        # If rececipient has not been saved before
                        if alreadySaved == False:
                            electricityBeneficiary.append(
                                {
                                    "operator":selectedOperatorName,
                                    "smartcardNumber":smartcardNumber,
                                    "customerName":customerName,
                                }
                            ) 
                            userBeneficiaries.telecomms = electricityBeneficiary 
                            userBeneficiaries.save() 
                            print("New beneficary added")               
                        print(f"these are the current telecomms beneficiaries 2 {electricityBeneficiary}")
                        
                except ObjectDoesNotExist:
                    newBeneficiary = [{
                        "operator":selectedOperatorName,
                        "smartcardNumber":smartcardNumber,
                        "customerName":customerName,
                        }]
                    # Create Beficiaryobject
                    Beneficiary.objects.create(
                        user = user,
                        telecomms = newBeneficiary
                    )

            # Todo Integrate electricity Services
            # airtimeServices = AirtimeServices.objects.get(network_operator=operator)
            # if airtimeServices.available == False:
            #     return JsonResponse({
            #         "code":"09",
            #         "message":f"{operator} airtime is currently unavailable"
            #     }) 


            # Todo First Check for duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,operator=selectedOperatorName,recipient=smartcardNumber,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
            if existingTran.count() > 0:
                return JsonResponse({
                    "code":"09",
                    "message":"Duplicate transaction wait 1 minute"
                })
            
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
            # print(responseDetails)
            
            if responseDetails['responseCode'] == '200':
                operatorData = responseDetails['data']
                bouquetList = []
                for entry in operatorData:
                    if entry['fieldName'] == 'itemId':
                        bouquetList = entry['items']
                        break
                # print(f"bouquet list is {bouqueList}")
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
                                transaction_type = "Cable",
                                comment = f"Cable {transRef}",
                                amount = Decimal(amount),
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
                                balanceBefore = balanceBefore,
                                balanceAfter = wallet.balance,
                            )
                
                            transaction.refresh_from_db()

                            user.last_transacted = datetime.now().date()
                            user.save()

                            # Second check for duplicate transaction
                            startTime = datetime.now() - timedelta(seconds=30) 
                            existingTran = Transaction.objects.filter(user=user,operator=selectedOperatorName,recipient=smartcardNumber,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
                            if existingTran.count() > 1:
                                return JsonResponse({
                                    "code":"09",
                                    "message":"Duplicate transaction wait 1 minute"
                                })
                            else:
                                cableBackend = CableBackend.objects.get(name='Main')
                                
                                # Buy from 9Payment Backend
                                if cableBackend.active_backend == "9Payment":
                                    
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
                                    print(f"9Payment response is {responseData}")
                                    
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
        APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODMwMTcwNiwianRpIjoiZGZjM2E3MzAtODA1NC00YmY1LTk3MzYtM2JjOWNlMGZlZTBlIiwiZXhwIjoxNzI4MzA4OTA2fQ.LiZofc-oj6WW9VdVIBmNsSR94Z1F7F9GfMiOcIZhknMLt6maAQaHK1eOKMHINalhTdb6Jf2omFx1agLXHvexLA"
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
        print(responseDetails)
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
            print(request.POST)
            accountId = request.POST.get("accountId")
            selectedOperator = request.POST.get("selectedOperator")
            selectedOperatorName = request.POST.get("selectedOperatorName")
            customerName = request.POST.get("customerName")
            otherField = request.POST.get("otherField")
            amount = Decimal(request.POST.get("amount"))
            print(f"sent amount is {amount}")
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
                            # print(entry)
                            # alreadySaved = True
                            if entry['accountId'] == accountId:
                                alreadySaved = True
                                print("Record already saved")
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
                            print("New beneficary added")               
                        print(f"these are the current telecomms beneficiaries 2 {betFundingBeneficiary}")
                        
                except ObjectDoesNotExist:
                    newBeneficiary = [{
                        "operator":selectedOperatorName,
                        "accountId":accountId,
                        "customerName":customerName,
                        }]
                    # Create Beficiaryobject
                    Beneficiary.objects.create(
                        user = user,
                        telecomms = newBeneficiary
                    )

            # Todo Integrate electricity Services
            # airtimeServices = AirtimeServices.objects.get(network_operator=operator)
            # if airtimeServices.available == False:
            #     return JsonResponse({
            #         "code":"09",
            #         "message":f"{operator} airtime is currently unavailable"
            #     }) 


            # Todo First Check for duplicate transaction  
            existingTran = Transaction.objects.filter(user=user,operator=selectedOperatorName,recipient=accountId,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
            if existingTran.count() > 0:
                return JsonResponse({
                    "code":"09",
                    "message":"Duplicate transaction wait 1 minute"
                })
            
            # Remove temp API KEY
            APIKEY = "eyJ0eXAiOiJKV1QiLCJrZXlJZCI6InZhc19qd3QiLCJhbGciOiJIUzUxMiJ9.eyJhdXRob3JpdGllcyI6WyJCSUxMU19QQVlNRU5UIiwiVE9QX1VQIl0sInN1YiI6IlZVVlUiLCJpc3MiOiI5cHNiLmNvbS5uZyIsImlhdCI6MTcyODMwMTcwNiwianRpIjoiZGZjM2E3MzAtODA1NC00YmY1LTk3MzYtM2JjOWNlMGZlZTBlIiwiZXhwIjoxNzI4MzA4OTA2fQ.LiZofc-oj6WW9VdVIBmNsSR94Z1F7F9GfMiOcIZhknMLt6maAQaHK1eOKMHINalhTdb6Jf2omFx1agLXHvexLA"
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
                existingTran = Transaction.objects.filter(user=user,operator=selectedOperatorName,recipient=accountId,amount=amount,created__gte=datetime.now() - timedelta(seconds=45))
                if existingTran.count() > 1:
                    return JsonResponse({
                        "code":"09",
                        "message":"Duplicate transaction wait 1 minute"
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
                            "billerId": "BET9JA",
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
                        print(f"9Payment response is {responseData}")
                        
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

