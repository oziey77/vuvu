from django.db import models

# Create your models here.


SERVICE_TYPE = (
    ("Cable","Cable"),
    ("Electricity","Electricity"),
)


class BillPaymentServices(models.Model):
    service_type = models.CharField(max_length=15,choices=SERVICE_TYPE)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.service_type