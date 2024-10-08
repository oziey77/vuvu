from django.urls import path
from . import views

urlpatterns = [
    path('buy-electricity/',views.electricityPage,name='buy-electricity'),
    path('pay-electricity/',views.buyElectricity,name='pay-electricity'),
    path('cable-page/',views.cablePage,name='cable-page'),
    path('bet-funding/',views.betFundingPage,name='bet-funding'),

    # AJAX
    path('validate-meter/',views.validateMeter),
    path('fetch-cable-bouquet/',views.getCableBouquet),
    path('validate-smartcard/',views.validateSmartcard),
    path('pay-cable-subscription/',views.buyCable),
    path('validate-bet-wallet/',views.validateBettingAccount),
    path('fund-bet-wallet/',views.fundBettingWallet),
]