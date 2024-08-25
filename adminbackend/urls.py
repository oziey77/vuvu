from django.urls import path
from . import views
urlpatterns=[
    path('overview/',views.overviewPage,name='overview'),
    path('users/',views.usersPage,name='all-users'),
    path('user-detail/<str:username>',views.userDetailPage,name='user-detail'),
    path('user-wallet-funding/<str:username>',views.userWalletundingPage,name='user-wallet-funding'),
]