from django.db import models

AIRTIME_BACKEND=(
    ("ATN","ATN"),
    ("TWINS10","TWINS10"),
    ("HONOURWORLD","HONOURWORLD"),
    )
class AirtimeBackend(models.Model):
    operator = models.CharField(max_length=10,default="Main")
    active_backend = models.CharField(max_length=15,choices=AIRTIME_BACKEND,default="ATN")

    def __str__(self):
        return self.operator

NETWORK_OPERATORS=(
    ("MTN","MTN"),
    ("Glo","Glo"),
    ("9Mobile","9Mobile"),
    ("Airtel","Airtel"),
    )
class AirtimeDiscount(models.Model):
    networkOperator = models.CharField(max_length=10,choices=NETWORK_OPERATORS)
    rate = models.DecimalField(max_digits=6,decimal_places=2)

    def __str__(self):
        return self.networkOperator
    
DATA_BACKEND=(
    ("ATN","ATN"),
    ("TWINS10","TWINS10"),
    ("HONOURWORLD","HONOURWORLD"),
    )
class DataBackend(models.Model):
    operator = models.CharField(max_length=10,choices=NETWORK_OPERATORS)
    active_backend = models.CharField(max_length=15,choices=DATA_BACKEND,default="ATN")

    def __str__(self):
        return self.operator
    

ELECTRICITY_BACKEND=(
    ("9Payment","9Payment"),
    ("SafeHaven","SafeHaven"),
    )
class ElectricityBackend(models.Model):
    name = models.CharField(max_length=10,default="Main")
    active_backend = models.CharField(max_length=15,choices=ELECTRICITY_BACKEND,default="9Payment")

    def __str__(self):
        return self.name
    
CABLE_BACKEND=(
    ("9Payment","9Payment"),
    ("SafeHaven","SafeHaven"),
    )
class CableBackend(models.Model):
    name = models.CharField(max_length=10,default="Main")
    active_backend = models.CharField(max_length=15,choices=CABLE_BACKEND,default="9Payment")

    def __str__(self):
        return self.name

EPIN_BACKEND=(
    ("9Payment","9Payment"),
    )    
class EPINBackend(models.Model):
    name = models.CharField(max_length=10,default="Main")
    active_backend = models.CharField(max_length=15,choices=EPIN_BACKEND,default="9Payment")

    def __str__(self):
        return self.name
    
class VuvuStory(models.Model):
    youtube_id= models.CharField(max_length=20)
    description = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.youtube_id
    

BILL_SERVICES=(
    ("Electricity","Electricity"),
    ("Cable","Cable"),
    ("Education","Education"),
    ("Betting","Betting"),
    )
class BillServicesDiscount(models.Model):
    service_type = models.CharField(max_length=25,choices=BILL_SERVICES)
    rate = models.DecimalField(max_digits=6,decimal_places=2)

    def __str__(self):
        return self.service_type
