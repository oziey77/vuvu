from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _

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


    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS =[]
    REQUIRED_FIELDS = ['username']

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
        return 0
    
    
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
    ("Transfer","Transfer"),
    ("Admin Deposit","Admin Deposit"),
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

    

