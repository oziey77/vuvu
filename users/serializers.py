from rest_framework import serializers

from users.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    # created = serializers.DateTimeField(format="%d/%b/%Y")
    created = serializers.DateTimeField(format="%d %B %Y %H:%M  ")
    # time = serializers.DateTimeField(format=" %H:%M  ")
    
    class Meta:
        model = Transaction
        fields = "__all__"