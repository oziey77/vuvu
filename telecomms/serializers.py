from rest_framework import serializers

from adminbackend.models import AirtimeDiscount
from telecomms.models import ATNDataPlans, HonouworldDataPlans, Twins10DataPlans


class AirtimeDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirtimeDiscount
        fields = ['id','networkOperator','rate',]

class ATNDataPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATNDataPlans
        fields = ['id','network_operator','plan','package_id','price','validity']

class HonouworldDataPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = HonouworldDataPlans
        fields = ['id','network_operator','plan','package_id','price','validity']

class Twins10DataPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Twins10DataPlans
        fields = ['id','network_operator','plan','package_id','price','validity']

        