from decimal import Decimal
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from django.core.exceptions import ObjectDoesNotExist

from adminbackend.models import AirtimeBackend, AirtimeDiscount, DataBackend
from telecomms.models import ATNDataPlans, AirtimeServices, DataServices, HonouworldDataPlans, Twins10DataPlans
from telecomms.serializers import ATNDataPlanSerializer, AirtimeDiscountSerializer, HonouworldDataPlanSerializer, Twins10DataPlanSerializer
from users.models import Beneficiary, Cashback, Transaction, TransactionPIN, UserWallet, WalletActivity
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
    # Telecomms Beneficiary
    telecommsBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            telecommsBeneficiaries = userBeneficiaries.telecomms
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'telecommsBeneficiaries':telecommsBeneficiaries,
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
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):       
        
        if totalWalletFunding > 0:
            print(request.POST)
            operator = request.POST.get('operator')
            recipient = request.POST.get('recipient')
            amount = Decimal(request.POST.get('amount'))
            wallet = UserWallet.objects.get(user=user)
            safeBeneficiary = request.POST.get('safeBeneficiary')

            # Safe Beneficiary Logic
            if safeBeneficiary == "on":
                try:
                    userBeneficiaries = Beneficiary.objects.get(user=user)
                    if userBeneficiaries is not None:
                        telecommsBeneficiary = userBeneficiaries.telecomms 
                        # Search of record already exist
                        alreadySaved = False
                        for entry in telecommsBeneficiary:
                            # print(entry)
                            # alreadySaved = True
                            if entry['recipient'] == recipient:
                                alreadySaved = True
                                print("Record already saved")
                                break
                        # If rececipient has not been saved before
                        if alreadySaved == False:
                            telecommsBeneficiary.append(
                                {
                                    "operator":operator,
                                    "recipient":recipient,
                                }
                            ) 
                            userBeneficiaries.telecomms = telecommsBeneficiary 
                            userBeneficiaries.save() 
                            print("New beneficary added")               
                        print(f"these are the current telecomms beneficiaries 2 {telecommsBeneficiary}")
                        
                except ObjectDoesNotExist:
                    newBeneficiary = [{
                        "operator":operator,
                        "recipient":recipient,
                        }]
                    # Create Beficiaryobject
                    Beneficiary.objects.create(
                        user = user,
                        telecomms = newBeneficiary
                    )


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
                        transRef = reference(26)
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

                            print(f'Honourworld Response is {responseDetails}')
                            if error['msg'] == 'Insufficient wallet fund':
                                return JsonResponse({
                                    "code":"09",
                                    "message":"network downtime!"
                                })
                            else:
                                return JsonResponse({
                                    "code":"09",
                                    "message":error["msg"]
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


# Airtime Page 
@login_required(login_url='login')
def dataPage(request):
    user = request.user
    wallet = UserWallet.objects.get(user=user)
    # Telecomms Beneficiary
    telecommsBeneficiaries = None
    try:
        userBeneficiaries = Beneficiary.objects.get(user=user)
        if userBeneficiaries is not None:
            telecommsBeneficiaries = userBeneficiaries.telecomms
    except ObjectDoesNotExist:
        pass
    context = {
        'mainBalance':wallet.balance,
        'telecommsBeneficiaries':telecommsBeneficiaries
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
                dataplans = ATNDataPlans.objects.filter(network_operator=operator).order_by("list_order")
                serializer = ATNDataPlanSerializer(dataplans,many=True)
                return JsonResponse({
                    "code":"00",
                    "activeBackend":activebackend,
                    "plans":serializer.data,
                })
            elif activebackend == "HONOURWORLD":
                dataplans = HonouworldDataPlans.objects.filter(network_operator=operator).order_by("id")
                serializer = HonouworldDataPlanSerializer(dataplans,many=True)
                extraPlans = None
                # Fetch extra ATN Data Plans
                # if operator == "MTN":
                extraData = ATNDataPlans.objects.filter(network_operator=operator,plan_type="Extra").order_by("list_order")
                if extraData.count() > 0:
                    extraDataSerializer = ATNDataPlanSerializer(extraData,many=True)
                    extraPlans = extraDataSerializer.data
                    

                return JsonResponse({
                    "code":"00",
                    "activeBackend":activebackend,
                    "plans":serializer.data,
                    "extraPlans":extraPlans,
                })
            elif activebackend == "TWINS10":
                dataplans = Twins10DataPlans.objects.filter(network_operator=operator).order_by("id")
                serializer = Twins10DataPlanSerializer(dataplans,many=True)
                extraPlans = None
                # Fetch extra ATN Data Plans
                # if operator == "MTN":
                extraData = ATNDataPlans.objects.filter(network_operator=operator,plan_type="Extra").order_by("list_order")
                if extraData.count() > 0:
                    extraDataSerializer = ATNDataPlanSerializer(extraData,many=True)
                    extraPlans = extraDataSerializer.data
                return JsonResponse({
                    "code":"00",
                    "activeBackend":activebackend,
                    "plans":serializer.data,
                    "extraPlans":extraPlans,
                })
            

# Ajax call to buy airtime
@login_required(login_url='login')
def buyData(request):
    user = request.user
    totalWalletFunding = user.total_wallet_funding

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "POST":   
        # transcationPin = request.POST.get('transcationPin')
        # transPin = TransactionPIN.objects.get(user=user)
        # if check_password(transcationPin,transPin.transaction_pin):

        if totalWalletFunding > 0:
            operator = request.POST.get('operator')
            recipient = request.POST.get('recipient')
            planID = request.POST.get('planID')
            offerType = request.POST.get('offerType')
            offerStatus = request.POST.get('offerStatus')
            offerDiscount = Decimal(5)
            
            
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
                dataType = "Normal"
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
                    if operator == "MTN":
                        try:
                            plan = ATNDataPlans.objects.get(package_id=planID)
                            if plan is not None:
                                selectedPlan = plan
                                dataType = "Extra"
                        except ObjectDoesNotExist:
                            try:
                                plan = HonouworldDataPlans.objects.get(package_id=planID)
                                if plan is not None:
                                    selectedPlan = plan
                            except ObjectDoesNotExist:
                                return JsonResponse({
                                'code':'09', 
                                'message':'selected plan is not valid'       
                            })
                    else:
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
                    if operator == "MTN":
                        try:
                            plan = ATNDataPlans.objects.get(package_id=planID)
                            if plan is not None:
                                selectedPlan = plan
                                dataType = "Extra"
                        except ObjectDoesNotExist:
                            try:
                                plan = Twins10DataPlans.objects.get(package_id=planID)
                                if plan is not None:
                                    selectedPlan = plan
                            except ObjectDoesNotExist:
                                return JsonResponse({
                                'code':'09', 
                                'message':'selected plan is not valid'       
                            })
                    else:
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

                # Process user offers
                print(f"New POST request {request.POST}")
                totalTransactions = user.transaction_count
                completeOffers = user.completed_offers
                # If user accept offer
                if offerStatus == "claimed":                    
                    if offerType == "storeRating" and (totalTransactions == 78 or totalTransactions == 80 ):
                        offerDiscount = Decimal(20)
                        if len(completeOffers) == 0:
                            userOffers = []
                            offerData = {
                                "storeRating":{
                                    "totalTrial":1,
                                    "status":"completed"
                                }
                            }
                            userOffers.append(offerData)
                            user.completed_offers = userOffers
                            user.save()
                        else:
                            if offerType == "storeRating":
                                offerIndex = 0
                                for offer in completeOffers:
                                    for key in offer:
                                        if key == 'storeRating':
                                            offerIndex = completeOffers.index(offer)
                                            rejectCount = completeOffers[offerIndex]['storeRating']['totalTrial']
                                            if rejectCount == 1:
                                                completeOffers[offerIndex]['storeRating']['totalTrial'] = 2
                                                completeOffers[offerIndex]['storeRating']['status'] = 'completed'
                                                user.completed_offers = completeOffers
                                                user.save()
                                            break
                            elif offerType == "trustPilot":
                                offerData = {
                                        "trustPilot":{
                                            "totalTrial":1,
                                            "status":"completed"
                                        }
                                    }
                                userOffers.append(offerData)
                                user.completed_offers = userOffers
                                user.save()

                #If user reject offer                
                if offerStatus == "rejected":
                    if offerType == "storeRating" and (totalTransactions == 78 or totalTransactions == 80 ):
                        if len(completeOffers) == 0:
                            userOffers = []
                            offerData = {
                                "storeRating":{
                                    "totalTrial":1,
                                    "status":"pending"
                                }
                            }
                            userOffers.append(offerData)
                            user.completed_offers = userOffers
                            user.save()
                        else:
                            offerIndex = 0
                            for offer in completeOffers:
                                for key in offer:
                                    if key == 'storeRating':
                                        offerIndex = completeOffers.index(offer)
                                        rejectCount = completeOffers[offerIndex]['storeRating']['totalTrial']
                                        if rejectCount == 1:
                                            completeOffers[offerIndex]['storeRating']['totalTrial'] = 2
                                            completeOffers[offerIndex]['storeRating']['status'] = 'completed'
                                            user.completed_offers = completeOffers
                                            user.save()
                                        break
                    elif offerType == "trustPilot" and totalTransactions == 80: 
                        offerData = {
                                "trustPilot":{
                                    "totalTrial":1,
                                    "status":"completed"
                                }
                            }
                        userOffers.append(offerData)
                        user.completed_offers = userOffers
                        user.save()

                # return JsonResponse({
                #     "code":"09",
                #     "message":"Testing ongoing",
                #     "data":user.completed_offers
                # })
                
                
                
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

                    if activeBackend == "ATN" or dataType == "Extra":
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
                                amount = offerDiscount
                            )
                            wallet.cashback += offerDiscount
                            wallet.save()


                            transaction.status = "Success"
                            transaction.discount = offerDiscount
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
                    elif activeBackend == "HONOURWORLD" and dataType == "Normal": 
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
                                amount = offerDiscount
                            )
                            wallet.cashback += offerDiscount
                            wallet.save()
                            
                            # Update transaction
                            transaction.status = "Success"
                            transaction.discount = offerDiscount
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
                    elif activeBackend == "TWINS10" and dataType == "Normal":
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

                        
                        print(f"Twins10 response is {data}")
                        if data['status'] == "success" or data['status'] == "processing":
                            Cashback.objects.create(
                                user = user,
                                transaction_type = 'Data',
                                message = f"Data {transaction.reference}",
                                amount = offerDiscount
                            )
                            wallet.cashback += offerDiscount
                            wallet.save()
                            
                            # Update transaction
                            transaction.status = "Success"
                            transaction.discount = offerDiscount
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


# Get Available offer
def getCurrentOffer(request):
    user = request.user

    # Check if user have ever made a deposit
    if is_ajax(request) and request.method == "GET":  
        totalTransactions = user.transaction_count
        # totalTransactions = 90

        print(f"total Transaction is  {totalTransactions}")
        completeOffers = user.completed_offers
        print(f"Total completed offers {len(completeOffers)}")
        
        if len(completeOffers) == 0:
            if totalTransactions ==78 or totalTransactions ==79:
                return JsonResponse({
                    "code":"00",
                    "currentOffer":"storeRating",
                    "discount":"20"
                })
        else:
            if totalTransactions == 78 or totalTransactions == 79:
                offerIndex = 0
                for offer in completeOffers:
                    for key in offer:
                        if key == 'storeRating':
                            offerIndex = completeOffers.index(offer)
                            rejectCount = completeOffers[offerIndex]['storeRating']['totalTrial']
                            if rejectCount == 1: #first attempt for store rating
                                return JsonResponse({
                                    "code":"00",
                                    "currentOffer":"storeRating",
                                    "discount":"20"
                                })
                            else:
                                return JsonResponse({
                                    "code":"04",
                                    "message":"on offer found",
                                })
                            break
            elif totalTransactions == 80:
                return JsonResponse({
                    "code":"00",
                    "currentOffer":"trustPilot",
                    "discount":"20"
                })
            else:
                return JsonResponse({
                    "code":"04",
                    "message":"on offer found",
                })


        