from django.db import models

# Create your models here.


from users.models import User

# Create your models here.

DEPOSIT_METHOD = (
        ("Transfer","Transfer"),
        ("Cashback","Cashback"),
        ("Referral Bonus","Referral Bonus"),
        ("Failed Deposit","Failed Deposit"),
    ) 

class WalletFunding(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    method = models.CharField(max_length=20,choices=DEPOSIT_METHOD,default="Transfer")
    amount = models.DecimalField(max_digits=20,decimal_places=2) 
    balanceBefore = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    balanceAfter = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)    
    sessionId = models.CharField(max_length=200)
    accountNumber = models.CharField(max_length=10)
    sourceAccountNumber = models.CharField(max_length=20)
    sourceAccountName = models.CharField(max_length=100)    
    created = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.user.username

PARTNER_BANK = (
        ("SafeHaven MFB","SafeHaven MFB"),
    )  

DEPOSIT_STATUS = (
        ("Pending","Pending"),
        ("Failed","Failed"),
        ("Completed","Completed"),
    ) 

class OneTimeDeposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    accountNumber = models.CharField(max_length=10)
    accountName = models.CharField(max_length=50)
    transactionAmount = models.IntegerField()  
    settledAmount = models.DecimalField(max_digits=10,decimal_places=2,default=0)  
    accountID = models.CharField(max_length=28)
    reference = models.CharField(max_length=20)  
    bankName = models.CharField(max_length=20,choices=PARTNER_BANK,default="SafeHaven MFB")
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10,choices=DEPOSIT_STATUS,default="Pending")

    def __str__(self):
        return self.user.username
    
class SafeHavenPaymentTransaction(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    transaction_id =  models.CharField(max_length=30)
    sessionId = models.CharField(max_length=40)
    creditAccountNumber = models.CharField(max_length=10)
    creditAccountName = models.CharField(max_length=100)
    debitAccountNumber = models.CharField(max_length=20)
    debitAccountName = models.CharField(max_length=100)
    paymentReference = models.CharField(max_length=200)
    narration = models.CharField(max_length=200)
    transactionAmount = models.CharField(max_length=10)
    settledAmount = models.CharField(max_length=10)
    feeAmount = models.CharField(max_length=10)
    vatAmount = models.CharField(max_length=10)
    currency = models.CharField(max_length=5,default='NGN')
    tranDateTime = models.CharField(max_length=30)
    status = models.CharField(max_length=20)    
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

SERVICE_STATUS = (
        ("Active","Active"),
        ("Disabled","Disabled"),
    )    

class PartnerBank(models.Model):
    bank_name = models.CharField(max_length=20,choices=PARTNER_BANK,default="SafeHaven MFB")
    deposit_charges = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    status = models.CharField(max_length=20,choices=SERVICE_STATUS,default="Active")
    def __str__(self):
        return self.bank_name


class DynamicAccountBackend(models.Model):
    name = models.CharField(max_length=10,default="Main")
    active_backend = models.CharField(max_length=20,choices=PARTNER_BANK,default="SafeHaven MFB")
    
    def __str__(self):
        return self.name

