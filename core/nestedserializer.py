from .models import Customer
from rest_framework import serializers

# customer serializer .1


# Read
class NestedCustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = (
            "id",
            "logo",
            "name",
            "address",
            "number",
            "email",
        )
        read_only_fields = fields
