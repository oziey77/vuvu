

import uuid
from django.core.exceptions import ObjectDoesNotExist
from users.models import User
from django.conf import settings
import requests

import csv
import json
# from users.tasks import createVirtualAccount

# # Providusbank auth details
# client_id = settings.CLIENT_ID
# authSignature = settings.PVD_XAUTH_SIGN

# OldVPSAccount.objects.all().delete() 
# User.objects.filter(admin=True).update(is_active=True)




def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def isNum(data):
    try:
        int(data)
        return True
    except ValueError:
        return False


def reference(string_length=12):
    # return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.


# Temporarily file writing
# Function to convert a CSV to JSON
# Takes the file paths as arguments
# def make_json(csvFilePath, jsonFilePath):
     
#     # create a dictionary
#     data = {}
     
#     # Open a csv reader called DictReader
#     with open(csvFilePath, encoding='utf-8') as csvf:
#         csvReader = csv.DictReader(csvf)
         
#         # Convert each row into a dictionary 
#         # and add it to data
#         for rows in csvReader:
             
#             # Assuming a column named 'No' to
#             # be the primary key
#             key = rows['account_number']
#             data[key] = rows
 
#     # Open a json writer, and use the json.dumps() 
#     # function to dump data
#     with open(jsonFilePath, 'w', encoding='utf-8') as jsonf:
#         jsonf.write(json.dumps(data, indent=4))
         
# # Driver Code
 
# # Decide the two file paths according to your 
# # computer system
# csvFilePath = r'yagapay/vpsaccounts.csv'
# jsonFilePath = r'yagapay/vpsaccounts.json'
 
# # Call the make_json function
# make_json(csvFilePath, jsonFilePath)
        