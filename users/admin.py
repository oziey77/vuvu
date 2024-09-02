from django.contrib import admin

from users.models import Cashback, Transaction, TransactionPIN, User, UserConfirmation, UserWallet, WalletActivity

# Register your models here.


class UserAdmin(admin.ModelAdmin):
    list_display = ['username','email','phone_number','referral_code','created','modified']
    search_fields = ['username','email','phone_number','referral_code',]
admin.site.register(User,UserAdmin)

class UserConfirmationAdmin(admin.ModelAdmin):
    list_display = ['user','confirmation_id','otp','created']
    search_fields = ['username__username','user__email',]
admin.site.register(UserConfirmation,UserConfirmationAdmin)

class UserWalletAdmin(admin.ModelAdmin):
    list_display = ['user','balance','cashback','referral_bonus']
    search_fields = ['username__username','user__email',]
admin.site.register(UserWallet,UserWalletAdmin)

class WalletActivityAdmin(admin.ModelAdmin):
    list_display = ['user','event_type','transaction_type','comment','amount','balanceBefore','balanceAfter',]
    search_fields = ['user__username']
admin.site.register(WalletActivity,WalletActivityAdmin)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user','transaction_type','operator','amount','balanceBefore','balanceAfter','created','status']
    search_fields = ['user__username','reference']
admin.site.register(Transaction,TransactionAdmin)


class CashbackAdmin(admin.ModelAdmin):
    list_display = ['user','transaction_type','amount','created']
    search_fields = ['user__username',]
admin.site.register(Cashback,CashbackAdmin)

admin.site.register(TransactionPIN)