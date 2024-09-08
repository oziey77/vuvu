from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse
from decimal import Decimal
from datetime import date, datetime, timedelta,timezone

import requests
import json

from payments.models import OneTimeDeposit, SafeHavenPaymentTransaction, WalletFunding
from users.models import SafeHavenAccount, UserWallet, WalletActivity
from vuvu.custom_functions import  is_ajax, reference

# Create your views here.
require_http_methods(['POST'])
@csrf_exempt      
def safeHavenWebhook(request):

    if request.method == "POST":
        response = json.loads(request.body)
        # decodedResponse = response[0]
        transferDetails = response['data']
        sessionID = transferDetails['sessionId']

        try:
            transaction = SafeHavenPaymentTransaction.objects.get(sessionId=sessionID)
            if transaction is not None:
                return HttpResponse(200)

        except ObjectDoesNotExist:
            # Get Access token
            clientID = settings.SAFEH_CLIENT_ID
            clientAssertion = settings.SAFEH_CLIENT_ASSERTION
            authToken = ''
            ibsClientID = ''

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
                ibsClientID = data['ibs_client_id']


                # VERIFY TRANSACTION
                url = "https://api.safehavenmfb.com/transfers/status"                                        
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization':f"Bearer {authToken}",
                    'ClientID':ibsClientID
                }

                payload = json.dumps({
                    "sessionId": sessionID
                })
                response = requests.request("POST", url, headers=headers, data=payload)
                
                responseData = json.loads(response.text)
                if responseData['statusCode'] == 200 and responseData['responseCode'] == "00":
                    transferData = responseData['data']
                    creditAccount = transferData['creditAccountNumber']

                    amount = Decimal(transferData['amount'])

                    settledAmount = Decimal(0)

                    if amount <= Decimal(1000):
                        settledAmount = amount - Decimal(10) #Backend Settled amount
                    elif amount > Decimal(1000) and amount <= Decimal(5000):
                        settledAmount = amount - Decimal(25) #Backend Settled amount
                    elif amount > Decimal(5000):
                        settledAmount = amount - Decimal(50) #Backend Settled amount

                    # Get savehaven account 
                    account = ''
                    try:                        
                        userAccount = SafeHavenAccount.objects.get(account_number=creditAccount)
                        if userAccount is not None:
                            account = userAccount 
                    except ObjectDoesNotExist:
                        pass




                    wallet = UserWallet.objects.get(user = account.user) # Get User wallet
                    balanceBefore = wallet.balance
                    user = account.user
                    transRef = reference()
                    # Create new payment Transactions
                    transaction = SafeHavenPaymentTransaction.objects.create(
                        user = user, 
                        transaction_id =  transferData['_id'],
                        sessionId = sessionID,
                        creditAccountNumber = transferData['creditAccountNumber'],
                        creditAccountName = transferData['creditAccountName'],
                        debitAccountNumber = transferData['debitAccountNumber'],
                        debitAccountName = transferData['debitAccountName'],
                        paymentReference = transferData['paymentReference'],
                        narration = transferData['narration'],
                        transactionAmount = transferData['amount'],
                        settledAmount = transferData['amount'] - transferData['fees'],
                        feeAmount = transferData['fees'],
                        vatAmount = transferData['vat'],
                        tranDateTime = transferData['createdAt'],
                        status = "Completed"                  
                    )
                    
                    wallet.balance += settledAmount # credit user wallet with amount deposited
                    wallet.save()

                    
                    # create wallet fundng object
                    WalletFunding.objects.create(
                        user=transaction.user,
                        method = "Transfer",
                        amount = settledAmount,
                        accountNumber = transferData['creditAccountNumber'],
                        sessionId = sessionID,
                        sourceAccountNumber = transferData['debitAccountNumber'],
                        sourceAccountName = transferData['debitAccountName'],
                        balanceBefore = balanceBefore,
                        balanceAfter = wallet.balance,
                        )
                    
                    # Create wallet Activity
                    WalletActivity.objects.create(
                        user = transaction.user,
                        event_type = "Credit",
                        transaction_type = 'Top Up',
                        comment = sessionID,
                        amount = settledAmount,
                        balanceBefore = balanceBefore,
                        balanceAfter = wallet.balance,
                    )

                    account.last_funded = datetime.now(timezone.utc)
                    account.save()
                    user.can_perform_transaction = True
                    user.save()
                    # send_deposit_invoice.delay(amount=transaction.settledAmount,email=user.email)# send invoice email
                    return HttpResponse(200)
        
        return HttpResponse(200)


require_http_methods(['POST'])
@csrf_exempt      
def safeHavenOneTimeWebhook(request):

    if request.method == "POST":
        response = json.loads(request.body)
        # decodedResponse = response[0]
        transferDetails = response['data']
        sessionID = transferDetails['sessionId']
        accountID = transferDetails['virtualAccount']
        extRef = transferDetails['externalReference']

        try:
            transaction = SafeHavenPaymentTransaction.objects.get(sessionId=sessionID)
            if transaction is not None:
                return HttpResponse(200)

        except ObjectDoesNotExist:
            try:
                pendingDeposit = OneTimeDeposit.objects.get(accountID=accountID,reference=extRef,status='Pending')
                if pendingDeposit is not None:
                    # Get Access token
                    clientID = settings.SAFEH_CLIENT_ID
                    clientAssertion = settings.SAFEH_CLIENT_ASSERTION
                    authToken = ''
                    ibsClientID = ''

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
                        ibsClientID = data['ibs_client_id']


                        # VERIFY TRANSACTION
                        url = "https://api.safehavenmfb.com/virtual-accounts/status"                                        
                        headers = {
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Authorization':f"Bearer {authToken}",
                            'ClientID':ibsClientID
                        }

                        payload = json.dumps({
                            "sessionId": sessionID
                        })
                        response = requests.request("POST", url, headers=headers, data=payload)
                        
                        responseData = json.loads(response.text)
                        if responseData['statusCode'] == 200 and responseData['responseCode'] == "00" and 'virtualAccount' in responseData['data']:
                            transferData = responseData['data']
                            creditAccount = transferData['creditAccountNumber']
                            oneAccountDetails = transferData['virtualAccount']

                            amount = Decimal(transferData['amount'])

                            settledAmount = Decimal(0)

                            if amount <= Decimal(1000):
                                settledAmount = amount - Decimal(10) #Backend Settled amount
                            elif amount > Decimal(1000) and amount <= Decimal(5000):
                                settledAmount = amount - Decimal(25) #Backend Settled amount
                            elif amount > Decimal(5000):
                                settledAmount = amount - Decimal(50) #Backend Settled amount

                            # Get savehaven account 
                            account = ''
                            try:                        
                                userAccount = OneTimeDeposit.objects.get(accountID=oneAccountDetails['_id'],reference=oneAccountDetails['externalReference'],status='Pending')
                                if userAccount is not None:
                                    account = userAccount 
                                    wallet = UserWallet.objects.get(user = account.user) # Get User wallet
                                    balanceBefore = wallet.balance
                                    user = account.user
                                    transRef = reference(12)
                                    # reference = reference
                                    # Create new payment Transactions
                                    transaction = SafeHavenPaymentTransaction.objects.create(
                                        user = user, 
                                        transaction_id =  transferData['_id'],
                                        sessionId = sessionID,
                                        creditAccountNumber = transferData['creditAccountNumber'],
                                        creditAccountName = transferData['creditAccountName'],
                                        debitAccountNumber = transferData['debitAccountNumber'],
                                        debitAccountName = transferData['debitAccountName'],
                                        paymentReference = transferData['paymentReference'],
                                        narration = transferData['narration'],
                                        transactionAmount = transferData['amount'],
                                        settledAmount = transferData['amount'] - transferData['fees'],
                                        feeAmount = transferData['fees'],
                                        vatAmount = transferData['vat'],
                                        tranDateTime = transferData['createdAt'],
                                        status = "Completed"                  
                                    )
                                    
                                    wallet.balance += settledAmount # credit user wallet with amount deposited
                                    wallet.save()

                                    # create wallet fundng object
                                    WalletFunding.objects.create(
                                        user=transaction.user,
                                        method = "Transfer",
                                        amount = settledAmount,
                                        accountNumber = transferData['creditAccountNumber'],
                                        sessionId = sessionID,
                                        sourceAccountNumber = transferData['debitAccountNumber'],
                                        sourceAccountName = transferData['debitAccountName'],
                                        balanceBefore = balanceBefore,
                                        balanceAfter = wallet.balance,
                                        )
                                    
                                    # Create wallet Activity
                                    WalletActivity.objects.create(
                                        user = transaction.user,
                                        event_type = "Credit",
                                        transaction_type = 'Top Up',
                                        comment = sessionID,
                                        amount = settledAmount,
                                        balanceBefore = balanceBefore,
                                        balanceAfter = wallet.balance,
                                    )
                                    account.status = "Completed"
                                    account.transactionAmount = int(transferData['amount'])
                                    account.settledAmount = settledAmount
                                    account.save()
                                    user.can_perform_transaction = True
                                    user.save()
                                    # send_deposit_invoice.delay(amount=transaction.settledAmount,email=user.email)# send invoice email
                                    return HttpResponse(200)
                            except ObjectDoesNotExist:
                                pass
            except ObjectDoesNotExist:
                pass
            
        
        return HttpResponse(200)
    

def getTransactionStatus(request):
    if is_ajax(request=request):
        accountID = request.GET.get('accountID')
        try:
            paymentDetails = OneTimeDeposit.objects.get(accountID=accountID)
            if paymentDetails is not None:
                return JsonResponse({
                    'code':'00',
                    'transactionStatus':paymentDetails.status,
                    'settledAmount':paymentDetails.settledAmount
                })

        except ObjectDoesNotExist:
            return JsonResponse({
                    'code':'03',
                    'message':'Transaction not found'
                })
