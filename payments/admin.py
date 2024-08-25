from django.contrib import admin

from payments.models import WalletFunding

# Register your models here.


class WalletFundingAdmin(admin.ModelAdmin):
    list_display = ['user','method','amount','balanceBefore','balanceAfter',]
    search_fields = ['user__username']
admin.site.register(WalletFunding,WalletFundingAdmin)