from decimal import Decimal
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Q,Sum
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.conf import settings
import requests
import json
from adminbackend.forms import AirtimeDiscountForm, NotificationForm, VuvuStoryForm
from adminbackend.models import AirtimeBackend, AirtimeDiscount, CableBackend, DataBackend, ElectricityBackend
from billpayments.models import BillPaymentServices
from payments.models import WalletFunding
from telecomms.forms import ATNDataPlanForm, HonourworldDataPlanForm, Twins10DataPlanForm
from telecomms.models import ATNDataPlans, AirtimeServices, DataServices, HonouworldDataPlans, Twins10DataPlans
from users.models import Notifications, Transaction, User, UserWallet, WalletActivity
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage
from datetime import datetime

from vuvu.custom_functions import is_ajax

# Create your views here.



# Overview Page
@login_required(login_url='login')
def overviewPage(request):
    user = request.user
    if user.is_staff:
        today = datetime.now()
        totalUsers = User.objects.filter().exclude(admin=True).count()
        transactions = Transaction.objects.all()
        totalRevenue =  transactions.filter(status='Success').aggregate(TOTAL = Sum('amount'))['TOTAL']
        usersWalletBalance =  UserWallet.objects.all().aggregate(TOTAL = Sum('balance'))['TOTAL']
        # Total Wallet funding
        totalFunding = 0
        walletFunfing = WalletFunding.objects.all()
        if walletFunfing.count() > 0:
            totalFunding =  walletFunfing.aggregate(TOTAL = Sum('amount'))['TOTAL']

        # Airtime Revenue
        
        airtimeRevenue = 0
        airtimeTransactions = transactions.filter(transaction_type="Airtime",status='Success')
        dailyAirtimeTransactions = transactions.filter(transaction_type="Airtime",created__date=today.date())
        if airtimeTransactions.count() > 0:
            airtimeRevenue =  airtimeTransactions.aggregate(TOTAL = Sum('amount'))['TOTAL']
        # Data Revenue
        dataRevenue = 0
        dataTransactions = transactions.filter(transaction_type="Data",status='Success')
        dailyDataTransactions = transactions.filter(transaction_type="Data",created__date=today.date())
        if dataTransactions.count() > 0:
            dataRevenue =  dataTransactions.aggregate(TOTAL = Sum('amount'))['TOTAL']
        # Cable Revenue
        cableRevenue = 0
        cableTransactions = transactions.filter(transaction_type="Cable",status='Success')
        dailyCableTransactions = transactions.filter(transaction_type="Cable",created__date=today.date())
        if cableTransactions.count() > 0:
            cableRevenue =  cableTransactions.aggregate(TOTAL = Sum('amount'))['TOTAL']
        # Electricity Revenue
        electricityRevenue = 0
        electricityTransactions = transactions.filter(transaction_type="Electricity",status='Success')
        dailyElectricityTransactions = transactions.filter(transaction_type="Electricity",created__date=today.date())
        if electricityTransactions.count() > 0:
            electricityRevenue =  electricityTransactions.aggregate(TOTAL = Sum('amount'))['TOTAL']
        context = {
           'totalUsers':totalUsers,
           'totalTrans':transactions.count(),
           'totalRevenue':totalRevenue,
           'totalFunding':totalFunding,
           'usersWalletBalance':usersWalletBalance,
           'airtimeRevenue':airtimeRevenue,
           'dataRevenue':dataRevenue,
           'cableRevenue':cableRevenue, 
           'electricityRevenue':electricityRevenue,          
           'dailyAirtimeTransactions':dailyAirtimeTransactions.count(),
           'dailyDataTransactions':dailyDataTransactions.count(),
           'dailyCableTransactions':dailyCableTransactions.count(),
           'dailyElectricityTransactions':dailyElectricityTransactions.count(),
           
           
        }
        return render(request,'adminbackend/overview.html',context)
    else:
        return HttpResponse("Invalid credentials")
    
# Fetch Balance from Twins10
@login_required(login_url='login')
def fetchTwins10Balance(request):
    user = request.user
    base64Key=settings.TWINS10_B64_KEY
    
    if user.is_staff: # only staff user(main admin can login)
    #Fetch Vendor Wallet
        url = "https://twins10.com/api/user" 
        headers = {
            'Authorization': f"Basic {base64Key}",
            }        
        
        try:
            response = requests.request('POST', url, headers=headers)
            details = json.loads(response.text)  
            
            if details["status"] == "success":
                balance = details["balance"]
                return JsonResponse({
                    'status':'success',
                    'data':balance,
                })
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                    'status':'failed',
                })

# Fetch Balance from Bloc
@login_required(login_url='login')
def fetchAirtimeNGBalance(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        # Fetch Airtime Ng Balance
        AIRTIME_NG = settings.AIRTIME_NG
        airtimeNigeriaAPI = 'Bearer '+ AIRTIME_NG
        airtimeNigeriaBalance = 'https://www.airtimenigeria.com/api/v1/balance/get'

        airtimeNGUrl = airtimeNigeriaBalance
        airtimeNGHeaders = {
            'Authorization': airtimeNigeriaAPI,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
            }
        
        try:
            response = requests.request('GET', airtimeNGUrl, headers=airtimeNGHeaders)
            data= response.json()
            vendorBalance = data['universal_wallet']
            if vendorBalance is not None:
                airtimeNGBalance = vendorBalance['balance']
                return JsonResponse({
                    'status':'success',
                    'data':airtimeNGBalance,
                })
                
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                    'status':'failed',
                })


# Fetch Balance from Bloc
@login_required(login_url='login')
def fetchHonourworldBalance(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        # Fetch Airtime Ng Balance
        honourAPIKey = f'Bearer {settings.HONOUR_API_KEY}'
        # HonourWorld API to purchase data
        url = 'https://vtuapi.honourworld.com/api/v2/wallet/manage-wallet-balance'
        payload = {
                }
        headers = {
                'Authorization': honourAPIKey,
                # 'Content-Type': 'application/json',
                # 'Accept': 'application/json'
                }
        
        try:
            response = requests.request('GET', url, headers=headers,data=payload)
            responseData= response.json()
            if 'msg' in responseData and responseData['msg'] == 'Wallet details successfully retrieved':
                data = responseData['data']
                honourBalance = data['available']
                return JsonResponse({
                    'status':'success',
                    'data':honourBalance,
                })
                
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                    'status':'failed',
                })
    
#Users  Overview Page
@login_required(login_url='login')
def usersPage(request):
    user = request.user
    if user.is_admin:
        allUsersRaw = User.objects.filter().exclude(admin=True).order_by('-created')

        if request.GET.get('search'):
            keyword = request.GET.get('search').strip().lower()
            try:
                customer =  User.objects.get(Q(username=keyword)|Q(email=keyword))
                if customer is not None:
                    return redirect('user-detail',customer.username)
            except ObjectDoesNotExist:
                messages.error(request,f"keyword '{keyword}' did not return any result")

        p = Paginator(allUsersRaw,10)
        page_number = request.GET.get('page')
        try:
            allUsers = p.get_page(page_number)
        except PageNotAnInteger:
            allUsers = p.page(1)
        except EmptyPage:
            allUsers = p.page(p.num_pages)


        context = {
           'allUsers':allUsers,
           'totalUser':allUsersRaw.count()
        }
        return render(request,'adminbackend/all-users.html',context)
    else:
        return HttpResponse("Invalid credentials")
    
# User Detials Page
@login_required(login_url='login')
def userDetailPage(request,username):
    user = request.user
    if user.is_admin:
        customer = User.objects.get(username=username)
        if request.method == "POST" and user.is_staff:
            transactionType = request.POST.get('transaction-type')
            sessionID = request.POST.get('session-id').strip()
            amount = request.POST.get('amount')
            # comment = request.POST.get('comment')
            # Get custome wallet
            customerWallet = UserWallet.objects.get(user=customer)
            balanceBefore = customerWallet.balance
            customerWallet.balance += Decimal(amount)
            customerWallet.save()

            # Create wallet Activity
            WalletActivity.objects.create(
                user = customer,
                event_type = "Credit",
                transaction_type = transactionType,
                comment = sessionID,
                amount = Decimal(amount),
                balanceBefore = balanceBefore,
                balanceAfter = customerWallet.balance,
            )
            messages.success(request,f'{amount} was successfully added to user wallet')
            try:
                fundRecord = WalletFunding.objects.get(user=customer,sessionId=sessionID)
                if fundRecord is not None:
                    pass
            except ObjectDoesNotExist:           
                WalletFunding.objects.create(
                    user = customer,
                    method = "Failed Deposit",
                    amount = amount,
                    balanceBefore = balanceBefore,
                    balanceAfter = customerWallet.balance,
                    sessionId = sessionID,
                    accountNumber = "0000",
                    sourceAccountNumber = "Vuvu",
                    sourceAccountName = "Vuvu Admin",
                )
            return redirect('user-detail',customer.username)


        context = {
           'customer':customer
        }
        return render(request,'adminbackend/user-detail.html',context)
    else:
        return HttpResponse("Invalid credentials")
    
# User Wallet Funding Page
@login_required(login_url='login')
def userWalletfundingPage(request,username):
    user = request.user
    if user.is_admin:
        walletfundingsRaw = WalletFunding.objects.filter(user__username = username).order_by('-id')

        p = Paginator(walletfundingsRaw,10)
        page_number = request.GET.get('page')
        try:
            walletFundings = p.get_page(page_number)
        except PageNotAnInteger:
            walletFundings = p.page(1)
        except EmptyPage:
            walletFundings = p.page(p.num_pages)
        context = {
            'walletFundings':walletFundings,
            'walletfundingsRaw':walletfundingsRaw,
            'username':username,
        }
        return render(request,'adminbackend/user-wallet-funding.html',context)

# User Wallet Funding Page
@login_required(login_url='login')
def userWalletActivityPage(request,username):
    user = request.user
    if user.is_admin:
        walletActivitiesRaw = WalletActivity.objects.filter(user__username = username).order_by('-id')

        p = Paginator(walletActivitiesRaw,10)
        page_number = request.GET.get('page')
        try:
            walletActivities = p.get_page(page_number)
        except PageNotAnInteger:
            walletActivities = p.page(1)
        except EmptyPage:
            walletActivities = p.page(p.num_pages)
        context = {
            'walletActivities':walletActivities,
            'walletActivitiesRaw':walletActivitiesRaw,
            'username':username,
        }
        return render(request,'adminbackend/user-wallet-activity.html',context)
# Airtime Backend Page
@login_required(login_url='login')
def airtimeBackendPage(request):
    user = request.user
    if user.is_staff: # only staff user(main admin can login)
        airtimeBackends = AirtimeBackend.objects.all().order_by("id")
        context = {
            "airtimeBackends":airtimeBackends
        }
        
        return render(request,"adminbackend/airtime-backends.html",context)   

# Update Airtime Backend
@login_required(login_url='login')
def updateAirtimeBackend(request,operator):
    user = request.user

    
    if user.is_staff: # only staff user(main admin can login)
        try:
            selectedBackend = AirtimeBackend.objects.get(operator=operator)
            if selectedBackend is not None:
                newBackend = request.POST.get("active_backend")
                selectedBackend.active_backend = newBackend
                selectedBackend.save()
                messages.success(request,f"active backend for {operator} set to {newBackend} successfully")
                return redirect("airtime-backends")
        except ObjectDoesNotExist:
            messages.error(request,"selected backend does not exist")
            return redirect("airtime-backends")

# Airtime Discount Page
@login_required(login_url='login')
def airtimeDiscountsPage(request):
    user = request.user
    
    if user.is_staff:
        airtimeDiscounts = AirtimeDiscount.objects.all().order_by('id')
        context = {
            'airtimeDiscounts':airtimeDiscounts,
        }
        return render(request,'adminbackend/airtime-discount.html',context)
    return redirect ('login')

#AIRTIME DISCOUNT UPDATE
@login_required(login_url='login')
def updateAirtimeDiscount(request):
    user = request.user

    if request.method == 'POST' and user.is_staff:
        operator = request.POST['networkOperator']
        try:
            instance = AirtimeDiscount.objects.get(networkOperator=operator)
            if instance is not None:
                form = AirtimeDiscountForm(request.POST,instance=instance)
                form.save()
                messages.success(request,f"airtime discount for {operator} successfully updated")
        except:
            pass
        return redirect('airtime-discounts')
    

# Manage Services
@login_required(login_url='login')
def manageServices(request):
    user = request.user    
    if user.is_staff: # only staff user(main admin can login)
        airtimeServices = AirtimeServices.objects.all().order_by('id')
        dataServices = DataServices.objects.all().order_by('id')
        billsPaymentServices = BillPaymentServices.objects.all().order_by('id')
        
        context = {
            'airtimeServices':airtimeServices,
            'dataServices':dataServices,
            'billsPaymentServices':billsPaymentServices,
        }
        return render(request,'adminbackend/services.html',context)
    
@login_required(login_url='login')
def updateService(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        
        if is_ajax(request=request) and request.method == "POST":
            serviceType  = request.POST.get('serviceType')
            operator  = request.POST.get('operator')
            
            # Disable/Enable Airtime
            if serviceType == "airtime":
                service = AirtimeServices.objects.get(network_operator=operator)
                if service.available == True:
                    service.available = False
                    service.save()
                    return JsonResponse({
                    'status':'success',
                    'available':service.available,
                    })
                elif service.available == False:
                    service.available = True
                    service.save()
                    return JsonResponse({
                        'status':'success',
                        'available':service.available,
                        })
                
            # Disable/Enable Data
            if serviceType == "data":
                service = DataServices.objects.get(network_operator=operator)
                if service.available == True:
                    service.available = False
                    service.save()
                    return JsonResponse({
                    'status':'success',
                    'available':service.available,
                    })
                elif service.available == False:
                    service.available = True
                    service.save()
                    return JsonResponse({
                        'status':'success',
                        'available':service.available,
                        })
                
            # Disable/Enable Bill Payments
            if serviceType == "bills":
                service = BillPaymentServices.objects.get(service_type=operator)
                if service.available == True:
                    service.available = False
                    service.save()
                    return JsonResponse({
                    'status':'success',
                    'available':service.available,
                    })
                elif service.available == False:
                    service.available = True
                    service.save()
                    return JsonResponse({
                        'status':'success',
                        'available':service.available,
                        })
                
            

# Data Backend Page
@login_required(login_url='login')
def dataBackendPage(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        dataBackends = DataBackend.objects.all().order_by("id")

        context = {
            "dataBackends":dataBackends
        }
        return render(request,"adminbackend/data-backends.html",context)

@login_required(login_url='login')
def updateDataBackend(request,operator):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        try:
            selectedBackend = DataBackend.objects.get(operator=operator)
            if selectedBackend is not None:
                newBackend = request.POST.get("active_backend")
                selectedBackend.active_backend = newBackend
                selectedBackend.save()
                messages.success(request,f"active backend for {operator} set to {newBackend} successfully")
                return redirect("data-backends")
        except ObjectDoesNotExist:
            messages.error(request,"selected backend does not exist")
            return redirect("data-backends")

# Electricity Backend Page
@login_required(login_url='login')
def electricityBackendPage(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        electricityBackend = ElectricityBackend.objects.get(name="Main")
        context = {
            "electricityBackend":electricityBackend
        }
        return render(request,"adminbackend/electricity-backends.html",context)

#Update 
@login_required(login_url='login')
def updateElectricityBackend(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        try:
            selectedBackend = ElectricityBackend.objects.get(name="Main")
            if selectedBackend is not None:
                newBackend = request.POST.get("active_backend")
                selectedBackend.active_backend = newBackend
                selectedBackend.save()
                messages.success(request,f"active backend for Electricity set to {newBackend} successfully")
                return redirect("electricity-backends")
        except ObjectDoesNotExist:
            messages.error(request,"selected backend does not exist")
            return redirect("electricity-backends")

# Cable Backend Page
@login_required(login_url='login')
def cableBackendPage(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        cableBackend = CableBackend.objects.get(name="Main")
        context = {
            "cableBackend":cableBackend
        }
        return render(request,"adminbackend/cable-backends.html",context)

# Update Cable Backend    
@login_required(login_url='login')
def updateCableBackend(request):
    user = request.user
    
    if user.is_staff: # only staff user(main admin can login)
        try:
            selectedBackend = CableBackend.objects.get(name="Main")
            if selectedBackend is not None:
                newBackend = request.POST.get("active_backend")
                selectedBackend.active_backend = newBackend
                selectedBackend.save()
                messages.success(request,f"active backend for Cable set to {newBackend} successfully")
                return redirect("cable-backends")
        except ObjectDoesNotExist:
            messages.error(request,"selected backend does not exist")
            return redirect("cable-backends")

# Transaction History
@login_required(login_url='login')
def transactionHistoryPage(request):
    user = request.user
    if user.is_admin:
        transactionRaw = Transaction.objects.all().order_by('-created')

        transactionType = 'All'
        if request.GET.get('filter'):
            key = request.GET.get('filter',None)
            transactionType = key
            transactionRaw = transactionRaw.filter(transaction_type=key.capitalize())

        if request.GET.get('search'):
            keyword = request.GET.get('search').strip().lower()
            try:
                customer =  User.objects.get(Q(username=keyword)|Q(email=keyword))
                if customer is not None:
                    return redirect('user-detail',customer.username)
            except ObjectDoesNotExist:
                messages.error(request,f"keyword '{keyword}' did not return any result")

        if request.GET.get('reference'):
            reference = request.GET.get('reference').strip().upper()
            try:                
                transaction = transactionRaw.get(reference=reference)
                if transaction is not None:
                    return redirect("transaction-detail",reference)
            except ObjectDoesNotExist:
                messages.error(request,f"reference '{reference}' did not return any result")

        p = Paginator(transactionRaw,10)
        page_number = request.GET.get('page')
        try:
            transactions = p.get_page(page_number)
        except PageNotAnInteger:
            transactions = p.page(1)
        except EmptyPage:
            transactions = p.page(p.num_pages)


        context = {
           'transactions':transactions,
           'totalTransactions':transactionRaw.count(),
           'transactionType':transactionType,
        }
        return render(request,'adminbackend/transaction-history.html',context)
    else:
        return HttpResponse("Invalid credentials")
    
# Transaction Detail Page
@login_required(login_url='login')
def transactionDetailPage(request,reference):
    user = request.user
    if user.is_admin:
        transaction = Transaction.objects.get(reference=reference)
        context = {
           'transaction':transaction
        }
        return render(request,'adminbackend/transaction-detail.html',context)
    else:
        return HttpResponse("Invalid credentials")
    
# Transaction Detail Page
@login_required(login_url='login')
def refundTransaction(request,pk):
    user = request.user
    if user.is_staff:
        reference = ''
        try:
            transaction = Transaction.objects.get(id=pk,refunded=False)
            if transaction is not None:
                reference = transaction.reference
                wallet = UserWallet.objects.get(user=transaction.user)
                balanceBefore = wallet.balance

                transaction.status = "Refunded"
                transaction.message = "Transaction refunded"
                transaction.refunded = True
                transaction.save()

                refundedAmount = (transaction.amount - transaction.discount)
                wallet.balance += refundedAmount
                wallet.save()

                # Create wallet Activity
                WalletActivity.objects.create(
                    user = transaction.user,
                    event_type = "Credit",
                    transaction_type = transaction.transaction_type,
                    comment = f"{transaction.transaction_type} {transaction.reference} Refund",
                    amount = refundedAmount,
                    balanceBefore = balanceBefore,
                    balanceAfter = wallet.balance,
                )
                messages.success(request,f"transaction refund successfull")
                return redirect("transaction-detail",reference)
        except ObjectDoesNotExist:
            messages.error(request,f"transaction could not be refunded, please contact technical team")
            return redirect("transaction-detail",reference)


# Wallet Funding Page
@login_required(login_url='login')
def walletFundingPage(request):
    user = request.user
    if user.is_admin:
        walletFundingRaw = WalletFunding.objects.all().order_by('-created')

        customer = ''
        if request.GET.get('customer'):
            keyword = request.GET.get('customer').strip().lower()
            walletFundingRaw =  walletFundingRaw.filter(user__username=keyword)
            if walletFundingRaw.count() == 0:
                messages.error(request,f"no wallet funding record found for user'{keyword}'")
            elif walletFundingRaw.count() > 0 :
                customer = keyword


        p = Paginator(walletFundingRaw,10)
        page_number = request.GET.get('page')
        try:
            walletFundings = p.get_page(page_number)
        except PageNotAnInteger:
            walletFundings = p.page(1)
        except EmptyPage:
            walletFundings = p.page(p.num_pages)


        context = {
           'walletFundings':walletFundings,
           'totalUser':walletFundingRaw.count(),
           'customer':customer,
        }
        return render(request,'adminbackend/wallet-funding.html',context)
    else:
        return HttpResponse("Invalid credentials")   

# ATN Data Plan Management
@login_required(login_url='login')
def ATNDataManagement(request):
    user = request.user
    selectedOperator = "Glo"
    
    if user.is_staff: # only staff user(main admin can login)

    # vault = TelecomsVault.objects.get(name='Telecommunication')
    # vendorBalance = '0.00'
    
        dataDiscounts = ATNDataPlans.objects.all().order_by('id')
        currentDataOperator = ATNDataPlans.objects.filter(network_operator=selectedOperator).order_by('id')
        if request.GET.get('filter'):
            print("We entered here")
            key = request.GET.get('filter',None)
            selectedOperator = key
            currentDataOperator = ATNDataPlans.objects.filter(network_operator=selectedOperator).order_by('id')

        context = {
        'dataDiscounts':dataDiscounts,
        'currentDataOperator':currentDataOperator,
        }
        return render(request,'adminbackend/atn-data-plans.html',context)
    return redirect('login')   
 
# Bulk Update ATN data plans
@login_required(login_url='login')
def bulkATNPlansUpdate(request):
    user = request.user
    if request.method == 'POST':
    
        if user.is_staff: # only staff user(main admin can login)
            operator = request.POST.get('networkOperator')
            action = request.POST.get('action')
            updateAmount = request.POST.get('amount')

            ratesToChange = ATNDataPlans.objects.filter(network_operator=operator)

            for rate in ratesToChange:
                if action == 'Add':
                    rate.price += Decimal(updateAmount)
                    rate.save()
                elif action == 'Substract':
                    rate.price -= Decimal(updateAmount)
                    rate.save()
            messages.success(request,f"{updateAmount} was successfully {action.lower()}ed to all {operator} plans")
            return redirect('atn-data-management')
        return redirect('atn-data-management')

#Update selected ATN plan
@login_required(login_url='login')
def updateATNDataPlan(request):
    user = request.user

    if request.method == 'POST':
    
        if user.is_staff: # only staff user(main admin can login)
            plan = request.POST['plan']
            # instance = DataDiscount.objects.get(plan=plan)
            try:
                instance = ATNDataPlans.objects.get(id=plan)
                if instance is not None:
                    form = ATNDataPlanForm(request.POST,instance=instance)
                    package = form.save()
                    messages.success(request,f"{package.network_operator} {package.plan} price was successfully set to {package.price}")
            except:
                pass
        return redirect('atn-data-management')
    return redirect('login')

# TWINS10 Data Plan Management
@login_required(login_url='login')
def twins10DataManagement(request):
    user = request.user
    selectedOperator = "Glo"
    
    if user.is_staff: # only staff user(main admin can login)

    # vault = TelecomsVault.objects.get(name='Telecommunication')
    # vendorBalance = '0.00'
    
        dataDiscounts = Twins10DataPlans.objects.all().order_by('id')
        currentDataOperator = Twins10DataPlans.objects.filter(network_operator=selectedOperator).order_by('id')
        if request.GET.get('filter'):
            key = request.GET.get('filter',None)
            selectedOperator = key
            currentDataOperator = Twins10DataPlans.objects.filter(network_operator=selectedOperator).order_by('id')

        context = {
        'dataDiscounts':dataDiscounts,
        'currentDataOperator':currentDataOperator,
        }
        return render(request,'adminbackend/twins10-data-plans.html',context)
    return redirect('login')  
  
# Bulk update Twins10 data plans
@login_required(login_url='login')
def bulkTwins10PlansUpdate(request):
    user = request.user
    if request.method == 'POST':
    
        if user.is_staff: # only staff user(main admin can login)
            operator = request.POST.get('networkOperator')
            action = request.POST.get('action')
            updateAmount = request.POST.get('amount')

            ratesToChange = Twins10DataPlans.objects.filter(network_operator=operator)

            for rate in ratesToChange:
                if action == 'Add':
                    rate.price += Decimal(updateAmount)
                    rate.save()
                elif action == 'Substract':
                    rate.price -= Decimal(updateAmount)
                    rate.save()
            messages.success(request,f"{updateAmount} was successfully {action.lower()}ed to all {operator} plans")
            return redirect('twins10-data-management')
        return redirect('twins10-data-management')

#Update selected Twins10 data plan
@login_required(login_url='login')
def updateTwins10DataPlan(request):
    user = request.user

    if request.method == 'POST':
    
        if user.is_staff: # only staff user(main admin can login)
            plan = request.POST['plan']
            # instance = DataDiscount.objects.get(plan=plan)
            try:
                instance = Twins10DataPlans.objects.get(id=plan)
                if instance is not None:
                    form = Twins10DataPlanForm(request.POST,instance=instance)
                    package = form.save()
                    messages.success(request,f"{package.network_operator} {package.plan} price was successfully set to {package.price}")
            except:
                pass
        return redirect('twins10-data-management')
    return redirect('login')

# TWINS10 Data Plan Management
@login_required(login_url='login')
def honourworldDataManagement(request):
    user = request.user
    selectedOperator = "Glo"
    
    if user.is_staff: # only staff user(main admin can login)

    # vault = TelecomsVault.objects.get(name='Telecommunication')
    # vendorBalance = '0.00'
    
        dataDiscounts = HonouworldDataPlans.objects.all().order_by('id')
        currentDataOperator = HonouworldDataPlans.objects.filter(network_operator=selectedOperator).order_by('id')
        if request.GET.get('filter'):
            key = request.GET.get('filter',None)
            selectedOperator = key
            currentDataOperator = HonouworldDataPlans.objects.filter(network_operator=selectedOperator).order_by('id')

        context = {
        'dataDiscounts':dataDiscounts,
        'currentDataOperator':currentDataOperator,
        }
        return render(request,'adminbackend/honourworld-data-plans.html',context)
    return redirect('login')  
  
# Bulk update Twins10 data plans
@login_required(login_url='login')
def bulkHonourworldPlansUpdate(request):
    user = request.user
    if request.method == 'POST':
    
        if user.is_staff: # only staff user(main admin can login)
            operator = request.POST.get('networkOperator')
            action = request.POST.get('action')
            updateAmount = request.POST.get('amount')

            ratesToChange = HonouworldDataPlans.objects.filter(network_operator=operator)

            for rate in ratesToChange:
                if action == 'Add':
                    rate.price += Decimal(updateAmount)
                    rate.save()
                elif action == 'Substract':
                    rate.price -= Decimal(updateAmount)
                    rate.save()
            messages.success(request,f"{updateAmount} was successfully {action.lower()}ed to all {operator} plans")
            return redirect('honourworld-data-management')
        return redirect('honourworld-data-management')

#Update selected Twins10 data plan
@login_required(login_url='login')
def updateHonourworldDataPlan(request):
    user = request.user

    if request.method == 'POST':
    
        if user.is_staff: # only staff user(main admin can login)
            plan = request.POST['plan']
            # instance = DataDiscount.objects.get(plan=plan)
            try:
                instance = HonouworldDataPlans.objects.get(id=plan)
                if instance is not None:
                    form = HonourworldDataPlanForm(request.POST,instance=instance)
                    package = form.save()
                    messages.success(request,f"{package.network_operator} {package.plan} price was successfully set to {package.price}")
            except:
                pass
        return redirect('honourworld-data-management')
    return redirect('login')

# Notification Management
@login_required(login_url='login')
def notificationsSetup(request):
    user = request.user    
    if user.is_staff: # only staff user(main admin can login)
        return render(request,'adminbackend/notification-setup.html')
    return redirect('login') 

# Send General Notification
@login_required(login_url='login')
def sendGeneralNotification(request):
    user = request.user    
    if user.is_staff and request.method == "POST": # only staff user(main admin can login)
        form = NotificationForm(request.POST)
        if form.is_valid():
            notificationData = form.save(commit=False)
            customers = User.objects.all().exclude(admin=True)
            print(f"Total users are {customers.count()}")
            for customer in customers:
                Notifications.objects.create(
                    user = customer,
                    title = notificationData.title,
                    body = notificationData.body
                )
            messages.success(request,"notifications sent successfully")
        else:
            print(form.errors)
            messages.error(request,"notifications failed to send")
        
        return redirect("notifications-management")
    return redirect('login') 

# Add Story Page
@login_required(login_url='login')
def vuvuStoryPage(request):
    user = request.user    
    if user.is_staff: # only staff user(main admin can login)
        if request.method == "POST": # only staff user(main admin can login)
            form = VuvuStoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request,"new story added successfully")
            else:
                print(form.errors)
                messages.error(request,"could not be added at the moment")
            return redirect("add-story")
        return render(request,'adminbackend/vuvu-story.html')
    return redirect('login') 

# @login_required(login_url='login')
# def saveStory(request):
#     user = request.user    
#     if user.is_staff and request.method == "POST": # only staff user(main admin can login)
#         form = VuvuStoryForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request,"new story added successfully")
#         else:
#             print(form.errors)
#             messages.error(request,"could not be added at the moment")
        
#         return redirect("notifications-management")
#     return redirect('login') 






    