from decimal import Decimal
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages

from payments.models import WalletFunding
from users.models import User, UserWallet, WalletActivity
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage

# Create your views here.



# Overview Page
@login_required(login_url='login')
def overviewPage(request):
    user = request.user
    if user.is_staff:
        totalUsers = User.objects.filter().exclude(admin=True).count()
        context = {
           'totalUsers':totalUsers,
        }
        return render(request,'adminbackend/overview.html',context)
    else:
        return HttpResponse("Invalid credentials")
    
# Overview Page
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
    
# Overview Page
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
def userWalletundingPage(request,username):
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
        }
        return render(request,'adminbackend/user-wallet-funding.html',context)

