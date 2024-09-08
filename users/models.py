from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from django.utils import timezone

from .managers import CustomUserManager

# Create your models here.

ACCOUNT_TYPE = (
    ("Premium","Premium"),
    ("Standard","Standard")
    ) 


class User(AbstractBaseUser):
    phone_number = models.CharField(max_length=11,unique=True)
    first_name = models.CharField(max_length=50,)
    last_name = models.CharField(max_length=50,)
    username = models.CharField(max_length=25,unique=True)
    email = models.EmailField(_('email address'), unique=True)    
    email_verified = models.BooleanField(default=False)
    can_perform_transaction = models.BooleanField(default=False) # a superuser
    is_active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False) # a admin user; non super-user
    admin = models.BooleanField(default=False) # a superuser
    created = models.DateField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    referral_code = models.CharField(max_length=15,null=True,blank=True,default='')
    referred_by = models.CharField(max_length=15,null=True,blank=True,default='')
    login_attempts_left = models.IntegerField(default=3)
    last_transacted = models.DateField(default=timezone.now)
    has_VPSAccount = models.BooleanField(default=False) # a superuser
    has_safeHavenAccount = models.BooleanField(default=False) # a superuser
    VPSAccount_reassigned = models.BooleanField(default=False)

    bvn_verified = models.BooleanField(default=False)
    nin_verified = models.BooleanField(default=False)

    vps_account_number = models.CharField(max_length=10,default='',blank=True)
    safeHavenAccount_account_number = models.CharField(max_length=10,default='',blank=True)
    safeHavenAccount_account_id = models.CharField(max_length=30,default='',blank=True)


    USERNAME_FIELD = 'username'
    # REQUIRED_FIELDS =[]
    # REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.staff

    @property
    def is_admin(self):
        "Is the user a admin member?"
        return self.admin
    
    @property
    def wallet_balances(self):
        wallet = UserWallet.objects.get(user=self)
        walletInfo = {
            'balance': wallet.balance,
            'cashback': wallet.cashback,
            'referral_bonus': wallet.referral_bonus,
        }
        return walletInfo
    
    @property
    def transaction_count(self):
        transactions = Transaction.objects.filter(user=self)           
        return transactions.count()
    
    @property
    def successful_transaction_value(self):
        total = 0
        transactions = Transaction.objects.filter(user=self,status='Success')
        if transactions.count() > 0:
            total = transactions.aggregate(TOTAL = Sum('amount'))['TOTAL']            
        return total
    
    @property
    def total_wallet_funding(self):
        from payments.models import WalletFunding
        deposits = WalletFunding.objects.filter(user=self)
        total = 0
        if deposits is not None:
            total = deposits.aggregate(TOTAL = Sum('amount'))['TOTAL']
        return total
    
    
    objects = CustomUserManager()


CONFIMATION_TYPE = (
    ("Email","Email"),
    ("OTP","OTP"),
)
class UserConfirmation(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    confirmation_id = models.CharField(max_length=16)
    otp = models.CharField(max_length=6)
    confirmation_type = models.CharField(max_length=10,choices=CONFIMATION_TYPE,default='Email')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class TransactionPIN(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    transaction_pin = models.CharField(max_length=200, null=True,blank=True)
    def __str__(self):
        return self.user.username
    
class UserWallet(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    cashback = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    referral_bonus = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)

    def __str__(self):
        return self.user.username
    

EVENT_TYPE = (
    ("Debit","Debit"),
    ("Credit","Credit"),
)
TRANSACTION_TYPE = (
    ("Airtime","Airtime"),
    ("Data","Data"),
    ("Cable","Cable"),
    ("Electricity","Electricity"),
    ("Top Up","Top Up"),
    ("Admin Top Up","Admin Top Up"),
    ("Cashback Withdrwal","Cashback Withdrwal"),
    ("Referral Bonus","Referral Bonus"),
)
class WalletActivity(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    event_type = models.CharField(max_length=10,choices=EVENT_TYPE)
    transaction_type = models.CharField(max_length=20,choices=TRANSACTION_TYPE)
    comment = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    balanceBefore = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    balanceAfter = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username



SERVICE_TYPE = (
    ("Airtime","Airtime"),
    ("Data","Data"),
    ("Cable","Cable"),
    ("Electricity","Electricity"),
)
TRANSACTION_STATUS = (
    ("Processing","Processing"),
    ("Success","Success"),
    ("Refunded","Refunded"),
)
API_BACKEND=(
    ("ATN","ATN"),
    ("TWINS10","TWINS10"),
    ("HONOURWORLD","HONOURWORLD"),
    )
class Transaction(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    message = models.CharField(max_length=500,default='No feedback')
    operator = models.CharField(max_length=10,)
    transaction_type = models.CharField(max_length=20,choices=SERVICE_TYPE)
    recipient = models.CharField(max_length=20,)
    APIBackend = models.CharField(max_length=15,choices=SERVICE_TYPE,default='-')
    APIreference = models.CharField(max_length=50,default='-')
    reference = models.CharField(max_length=26)
    package = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    discount = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    balanceBefore = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    balanceAfter = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    created = models.DateTimeField(auto_now_add=True)
    refunded = models.BooleanField(default=False)    
    status = models.CharField(max_length=12,choices=TRANSACTION_STATUS,default='Processing')    

    def __str__(self):
        return self.user.username
    

class Cashback(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20,choices=SERVICE_TYPE)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    message = models.CharField(max_length=100,default='No feedback')
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username
    

ID_TYPE = (
    ("BVN","BVN"),
    ("NIN","NIN")
    )  
KYC_STATUS = (
    ("Pending","Pending"),
    ("Completed","Completed")
    )   
class KYCData(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    id_type = models.CharField(max_length=3,choices=ID_TYPE)
    id_num = models.CharField(max_length=15)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    dob = models.CharField(max_length=20)
    status = models.CharField(max_length=20,choices=KYC_STATUS,default="Pending") 

    def __str__(self):
        return self.user.username
    

# SafeHaven Account
class SafeHavenAccount(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    account_number = models.CharField(max_length=10)
    account_name = models.CharField(max_length=100)
    account_id = models.CharField(max_length=30)
    bank_name = models.CharField(max_length=100,default='SafeHaven MFB')
    external_Reference = models.CharField(max_length=16)     
    created = models.DateTimeField(auto_now_add=True)
    last_funded = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return self.user.username


