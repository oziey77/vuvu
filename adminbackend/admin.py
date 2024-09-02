from django.contrib import admin

from adminbackend.models import AirtimeBackend, AirtimeDiscount, DataBackend

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
