from django.urls import path
from . import views


urlpatterns=[
    path('buy-aritime/',views.airtimePage,name='buy-airtime')
]