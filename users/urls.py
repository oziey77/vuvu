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
    path('wallet/',views.walletPage,name='wallet'),
    path('support/',views.supportPage,name='support'),
    path('notifications/',views.notificationsPage,name='notifications'),
    path('delete-notifications/',views.deleteNotifications,name='delete-notifications'),
    path('delete-account/',views.deleteAccountPage,name='delete-account'),
    path('request-account-delete/',views.deleteAccount,name='request-account-delete'),
    path("cancel-account-delete/",views.cancelAccountDelete,name="cancel-account-delete"),
    

    # Ajax Calls    
    path("resend-registration-code/",views.resendRegOTP),
    path("verify-registration/",views.verifyRegistration),
    path('user-balance/',views.fetchWalletBalance),
    path('logout',views.logoutUser,name='logout'),
    path('trasnsaction-detail/<str:pk>',views.getTransactionDetails),
    path('change-password/',views.changePassword),
    path('send-otp/',views.sendOTP),
    path('reset-password/',views.resetPassword),
    path('save-pin/',views.saveTransactionPin),
    path('check-pin/',views.checkTransactionPin),
    path('update-pin/',views.updateTransactionPin),
    path('onetime-topup/',views.dynamicAccountAmount),
    path("submit-kyc/",views.submitKYC),
    path("validate-kyc/",views.validateKYC),
    path("redeem-cashback/",views.redeemCashback),
    path("claim-giveaway/",views.claimGiveAway),
    
]