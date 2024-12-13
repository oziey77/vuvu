from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail
from celery import shared_task
import requests
import json

from adminbackend.models import AirtimeBackend, DataBackend


#API KEYS
AIRTIME_NG = settings.AIRTIME_NG
airtimeNigeriaAPI = 'Bearer '+ AIRTIME_NG

airtimeNigeriaBalance = 'https://www.airtimenigeria.com/api/v1/balance/get'


@shared_task
def checkAirtimeNgBalance():
    minLimit = Decimal(30000.00)
    url = airtimeNigeriaBalance
    headers = {
        'Authorization': airtimeNigeriaAPI,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
        }

    try:
        response = requests.request('GET', url, headers=headers)
        data= response.json()
        vendorBalance = data['universal_wallet']
        if vendorBalance is not None:
            if Decimal(vendorBalance['balance']) <= 1500:
                DataBackend.objects.filter(active_backend="ATN").update(active_backend="TWINS10")
                AirtimeBackend.objects.filter(active_backend="ATN").update(active_backend="TWINS10")
                
            if Decimal(vendorBalance['balance']) <= minLimit:
                subject = 'Vendor Balance Low'
                message = f"This is to inform you that your vendor balance with Airtime Nigeria is low:NGN {vendorBalance['balance']}. Please recharge as soon as possible to prevent service disruption."
                email_from =  'Vuvu <no-reply@vuvu.ng>'
                recipient_list = ['oluwatobi.otusanya@gmail.com','theolaseni@gmail.com']
                send_mail(subject,message,email_from,recipient_list)

            
    except requests.exceptions.RequestException as e:
        pass
