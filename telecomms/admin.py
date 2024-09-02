from django.contrib import admin

from telecomms.models import ATNDataPlans, AirtimeServices, DataServices, HonouworldDataPlans, Twins10DataPlans

# Register your models here.

class DataServicesAdmin(admin.ModelAdmin):
    list_display = ("network_operator", "available",)
admin.site.register(DataServices, DataServicesAdmin)
admin.site.register(AirtimeServices, DataServicesAdmin)



class DataPlansAdmin(admin.ModelAdmin):
    list_display = ("network_operator","plan","package_id","vendor_price", "price","validity")
    search_fields = ('network_perator',)
admin.site.register(ATNDataPlans, DataPlansAdmin)
admin.site.register(HonouworldDataPlans, DataPlansAdmin)
admin.site.register(Twins10DataPlans, DataPlansAdmin)

