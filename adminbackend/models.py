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
