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
