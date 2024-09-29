from django.db import models

from users.models import User

# Create your models here.




NETWORK_OPERATORS = (
    ("MTN","MTN"),
    ("Glo","Glo"),
    ("Airtel","Airtel"),
    ("9Mobile","9Mobile"),
)


class AirtimeServices(models.Model):
    network_operator = models.CharField(max_length=10,choices=NETWORK_OPERATORS)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.network_operator
    

class DataServices(models.Model):
    network_operator = models.CharField(max_length=10,choices=NETWORK_OPERATORS)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.network_operator

PLAN_TYPE = (
    ("Normal","Normal"),
    ("Extra","Extra"),
)    

class ATNDataPlans(models.Model):
    network_operator = models.CharField(max_length=10,choices=NETWORK_OPERATORS)
    plan = models.CharField(max_length=50,default='')    
    package_id = models.CharField(max_length=50)    
    vendor_price = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    validity = models.CharField(max_length=10)
    available = models.BooleanField(default=True)
    list_order = models.IntegerField(default=0)
    plan_type = models.CharField(max_length=10,choices=PLAN_TYPE,default="Normal")
    
    def __str__(self):
        return self.network_operator
    
class HonouworldDataPlans(models.Model):
    network_operator = models.CharField(max_length=10,choices=NETWORK_OPERATORS)
    plan = models.CharField(max_length=50,default='')    
    package_id = models.CharField(max_length=50)    
    vendor_price = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    validity = models.CharField(max_length=10)
    available = models.BooleanField(default=True)
    list_order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.network_operator
    
class Twins10DataPlans(models.Model):
    network_operator = models.CharField(max_length=10,choices=NETWORK_OPERATORS)
    plan = models.CharField(max_length=50,default='')    
    package_id = models.CharField(max_length=50)    
    vendor_price = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    validity = models.CharField(max_length=10)
    available = models.BooleanField(default=True)
    list_order = models.IntegerField(default=0)
    
    def __str__(self):
        return self.network_operator