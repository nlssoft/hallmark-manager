#cls
from .models import User
from core.models import Profile

# import cls
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer

#tools
from rest_framework import serializers
from django.db import transaction



class CustomeCookieOnlyJwtSerializer(JWTSerializer):
    def to_representation(self, instance):
        response= super().to_representation(instance)
        response.pop('access', None)
        response.pop('refresh', None)
        return response


class CustomeRegisterSerializer(RegisterSerializer):
    number= serializers.CharField(max_length=15)
    company_name= serializers.CharField(max_length=255, required=False, allow_blank=True)
    company_address= serializers.CharField(max_length=600, required=False, allow_blank=True)
    office_number1= serializers.CharField(max_length=15, required=False, allow_blank=True)     
    office_number2= serializers.CharField(max_length=15, required=False, allow_blank=True)
    first_name= serializers.CharField(max_length=100) 
    last_name= serializers.CharField(max_length=100) 

    # things like username, password, email are already handle by dj_rest_auth we just need to set what is not!!!
 
    def save(self, request):
        with transaction.atomic():
            user = super().save(request)

            user.first_name = self.validated_data["first_name"]
            user.last_name = self.validated_data["last_name"]
            user.save()

            Profile.objects.create(
                owner=user,
                number=self.validated_data["number"],  # required, safe
                company_name=self.validated_data.get("company_name", ""),
                company_address=self.validated_data.get("company_address", ""),
                office_number1=self.validated_data.get("office_number1", ""),
                office_number2=self.validated_data.get("office_number2", ""),
            )

            return user

            
    

