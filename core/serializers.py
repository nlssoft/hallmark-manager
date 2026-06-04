from .models import Profile
from rest_framework import serializers


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "number",
            "company_name",
            "company_address",
            "office_number1",
            "office_number2",
        )
