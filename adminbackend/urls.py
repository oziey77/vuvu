from django.urls import path
from . import views
urlpatterns=[
    path('overview/',views.overviewPage,name='overview'),
    path('users/',views.usersPage,name='all-users'),
    path('user-detail/<str:username>',views.userDetailPage,name='user-detail'),
    path('user-wallet-funding/<str:username>',views.userWalletfundingPage,name='user-wallet-funding'),
    path('user-wallet-activities/<str:username>',views.userWalletActivityPage,name='user-wallet-activities'),
    path("airtime-backends/",views.airtimeBackendPage,name='airtime-backends'), 
    path("update-airtime-backend/<str:operator>",views.updateAirtimeBackend,name="update-airtime-backend"),
    path('airtime-discounts/',views.airtimeDiscountsPage,name='airtime-discounts'),    
    path("update-airtime-discount/",views.updateAirtimeDiscount,name="update-airtime-discount"),
    path("services/",views.manageServices,name='services'),
    path("data-backends/",views.dataBackendPage,name='data-backends'),
    path("update-data-backend/<str:operator>",views.updateDataBackend,name="update-data-backend"),
    path("transactions/",views.transactionHistoryPage,name='transactions'),
    path('transaction-detail/<str:reference>',views.transactionDetailPage,name='transaction-detail'),
    path('refund-transaction/<str:pk>',views.refundTransaction,name='refund-transaction'),
    path('wallet-fundings/',views.walletFundingPage,name='wallet-fundings'),
    path("atn-data-management/",views.ATNDataManagement,name='atn-data-management'), 
    path("bulk-update-atn",views.bulkATNPlansUpdate,name="bulk-update-atn"), 
    path("update-atn-plan/",views.updateATNDataPlan,name="update-atn-plan"),

    path("twins10-data-management/",views.twins10DataManagement,name='twins10-data-management'), 
    path("bulk-update-twins10",views.bulkTwins10PlansUpdate,name="bulk-update-twins10"), 
    path("update-twins10-plan/",views.updateTwins10DataPlan,name="update-twins10-plan"),

    path("honourworld-data-management/",views.honourworldDataManagement,name='honourworld-data-management'), 
    path("bulk-update-honourworld",views.bulkHonourworldPlansUpdate,name="bulk-update-honourworld"), 
    path("update-honourworld-plan/",views.updateHonourworldDataPlan,name="update-honourworld-plan"),
    
    # Ajax
    path("update-services/",views.updateService),
    path("twins10-balance/",views.fetchTwins10Balance),
    path("airtimeng-balance/",views.fetchAirtimeNGBalance),
    path("honourworld-balance/",views.fetchHonourworldBalance),
]