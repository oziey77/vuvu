from django.contrib import admin

from adminbackend.models import AirtimeBackend, AirtimeDiscount, CableBackend, DataBackend, EPINBackend, ElectricityBackend
from billpayments.models import BillPaymentServices
from users.models import Notifications

# Register your models here.
class AirtimeBackendAdmin(admin.ModelAdmin):
    list_display = ["operator","active_backend"]
admin.site.register(AirtimeBackend,AirtimeBackendAdmin)

class AirtimeDiscountAdmin(admin.ModelAdmin):
    list_display = ("networkOperator", "rate",)
admin.site.register(AirtimeDiscount, AirtimeDiscountAdmin)

class DataBackendAdmin(admin.ModelAdmin):
    list_display = ["operator","active_backend"]
admin.site.register(DataBackend,DataBackendAdmin)

admin.site.register(Notifications)
admin.site.register(ElectricityBackend)
admin.site.register(CableBackend)
admin.site.register(EPINBackend)
admin.site.register(BillPaymentServices)
