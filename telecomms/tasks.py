from decimal import Decimal
from django.conf import settings
import requests
import json

from celery import shared_task

from telecomms.models import ATNDataPlans



# @shared_task
# def updateDataPlans():
#     AIRTIME_NG = settings.AIRTIME_NG
#     airtimeNigeriaAPI = 'Bearer '+ AIRTIME_NG
#     #Fetch Vendor Wallet
#     url = "https://www.airtimenigeria.com/api/v1/data/plans"
#     headers = {
#         'Authorization': airtimeNigeriaAPI,
#         'Content-Type': 'application/json',
#         'Accept': 'application/json'
#         }

    
    
#     try:
#         response = requests.request('GET', url, headers=headers)
#         details= response.json()
#         # return HttpResponse("success")
#         if details['success'] == True and details['status'] == 'success':
#             dataPlans = details['data']

#             mtnDataDiscounts = ATNDataPlans.objects.filter(network_operator='MTN')
#             gloDataDiscounts = ATNDataPlans.objects.filter(network_operator='Glo')
#             airtelDataDiscounts = ATNDataPlans.objects.filter(network_operator='Airtel')
#             nineMobileDataDiscounts = ATNDataPlans.objects.filter(network_operator='9Mobile')

#             # print('Total dataplans is',len(dataPlans))
#             for i in range(0,len(dataPlans)):

#                 # Update MTN Data Plans
#                 if dataPlans[i]['network_operator'] == 'mtn':
#                     for item in mtnDataDiscounts:
#                         if item.package_id == dataPlans[i]['package_code']:
#                             apiPrice = dataPlans[i]['dealer_price']
#                             item.vendor_price = Decimal(apiPrice)
#                             item.price = Decimal(apiPrice + 20)
#                             item.save()
                
#                 # Update GLO Data Plans
#                 if dataPlans[i]['network_operator'] == 'glo':
#                     for item in gloDataDiscounts:
#                         if item.package_id == dataPlans[i]['package_code']:
#                             apiPrice = dataPlans[i]['dealer_price']
#                             item.vendor_price = Decimal(apiPrice)
#                             item.price = Decimal(apiPrice + 20)
#                             item.save()

#                 # Update Airtel Data Plans
#                 if dataPlans[i]['network_operator'] == 'airtel':
#                     for item in airtelDataDiscounts:
#                         if item.package_id == dataPlans[i]['package_code']:
#                             apiPrice = dataPlans[i]['dealer_price']
#                             item.vendor_price = Decimal(apiPrice)
#                             item.price = Decimal(apiPrice + 20)
#                             item.save()

#                 # Update 9Mobile Data Plans
#                 if dataPlans[i]['network_operator'] == '9mobile':
#                     for item in nineMobileDataDiscounts:
#                         if item.package_id == dataPlans[i]['package_code']:
#                             apiPrice = dataPlans[i]['dealer_price']
#                             item.vendor_price = Decimal(apiPrice)
#                             item.price = Decimal(apiPrice + 20)
#                             item.save()

#             print("ATN DATA PLANS UPDATE")

#     except requests.exceptions.RequestException as e:
#         pass