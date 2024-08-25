from django.shortcuts import render

# Create your views here.


# Password Reset Successful page
def airtimePage(request):
    return render(request,'telecomms/airtime.html')