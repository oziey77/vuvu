from django.urls import path

from payments import views

urlpatterns = [
    path('safehaven-webhook',views.safeHavenWebhook),
    path('safehaven-onetime-webhook',views.safeHavenOneTimeWebhook),
    path('transaction-status/',views.getTransactionStatus)
]