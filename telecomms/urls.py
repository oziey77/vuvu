from django.urls import path
from . import views


urlpatterns=[
    path('buy-airtime/',views.airtimePage,name='buy-airtime'),
    path('buy-data/',views.dataPage,name='buy-data'),


    # Ajax
    path('get-airtime-discounts/',views.getAirtimeDiscount),
    path('purchase-airtime/',views.buyAirtime),
    path('fetch-data-plans/',views.fetchDataPlans),
    path('purchase-data/',views.buyData),
    path('available-offer/',views.getCurrentOffer),

    # Callback URL
    path('telecomms-callback',views.airtimeNGCallback),
    
]