from django.contrib import admin

from users.models import User, UserConfirmation, UserWallet, WalletActivity

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
