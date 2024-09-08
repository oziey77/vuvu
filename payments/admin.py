from django.contrib import admin

from payments.models import OneTimeDeposit, WalletFunding

# Register your models here.


class WalletFundingAdmin(admin.ModelAdmin):
    list_display = ['user','method','amount','balanceBefore','balanceAfter',]
    search_fields = ['user__username']
admin.site.register(WalletFunding,WalletFundingAdmin)

class OneTimeDepositAdmin(admin.ModelAdmin):
    list_display = ['user','accountNumber','transactionAmount','reference','created','status']
    search_fields = ('user__username','accountNumber')
admin.site.register(OneTimeDeposit,OneTimeDepositAdmin)