from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('',views.loginPage,name='login'),
    path('signup/',views.signupPage,name='signup'),
    path('activate/<uidb64>/<token>/',views.activate, name='activate'),
    path('confirmation-sent/<str:confirmationID>',views.confirmEmailSent,name='confirmation-sent'),
    path('forgot-password/',views.forgotPasswordPage,name='forgot-password'),
    path('password-reset/',views.passwordResetSentPage,name='password-reset'),
    path('password-reset-successful/',views.passwordResetSuccessfulPage,name='password-reset-successful'),
    # 
    path('dashboard/',views.dashboardPage,name='dashboard'),
    path('transaction-history/',views.transactionHistoryPage,name='transaction-history'),
    path('settings/',views.settingsPage,name='settings'),
    

    # Ajax Calls
    path('user-balance/',views.fetchWalletBalance),
    path('logout',views.logoutUser,name='logout'),
    path('trasnsaction-detail/<str:pk>',views.getTransactionDetails),
    path('change-password/',views.changePassword),
    path('send-otp/',views.sendOTP),
    path('reset-password/',views.resetPassword),
    path('save-pin/',views.saveTransactionPin),
    path('update-pin/',views.updateTransactionPin),
    
]