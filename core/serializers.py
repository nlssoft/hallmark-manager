from user.serializers import ReadOnlyEmployeeSerializer
from .models import (
    Groups,
    Customer,
    Service,
    GroupRate,
    Record,
    Payment,
    AuditLog,
    Request,
)
from user.models import Employee
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone


# customer serializer .1
class CustomerNestedSerializer(serializers.ModelSerializer):

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


# group serializers
class GroupRateNestedSerializer(serializers.Serializer):
    service_id = serializers.IntegerField(source="service.id")
    service_name = serializers.CharField(source="service.name")
    service_rate = serializers.DecimalField(
        source="rate", max_digits=10, decimal_places=2
    )


class ReadOnlyGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(
        max_length=255, allow_blank=True, allow_null=True, required=False
    )  # keep or not keep
    services = GroupRateNestedSerializer(
        read_only=True, source="grouprate_set", many=True
    )
    customers = CustomerNestedSerializer(
        read_only=True, many=True, source="customer_set"
    )


class CustomerReadOnlyGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(
        max_length=255, allow_blank=True, allow_null=True, required=False
    )  # keep or not keep
    services = GroupRateNestedSerializer(
        read_only=True, source="grouprate_set", many=True
    )


class GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(
        max_length=255, allow_blank=True, allow_null=True, required=False
    )  # keep or not keep
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        required=False,
        allow_null=True,
    )
    rate = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["service"].queryset = Service.objects.filter(owner=request.user)

    def validate(self, attrs):
        service = attrs.get("service")
        rate = attrs.get("rate")
        if service is None or rate is None:
            raise ValidationError("Service and rate cant be none.")
        return attrs

    def create(self, validated_data):
        owner = self.context["request"].user
        service = validated_data.pop("service")
        rate = validated_data.pop("rate")
        with transaction.atomic():
            group = Groups.objects.create(**validated_data, owner=owner)
            GroupRate.objects.create(group=group, service=service, rate=rate)
            return group

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()

        service = validated_data.get("service")
        rate = validated_data.get("rate")

        if service is not None and rate is not None:

            GroupRate.objects.update_or_create(
                group=instance, service=service, defaults={"rate": rate}
            )

        return instance


class RemoveServiceGroupSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = GroupRate
        fields = ("id", "service")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["service"].queryset = Service.objects.filter(owner=request.user)


class sync_customerSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), many=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["customer"].queryset = Customer.objects.filter(
                owner=request.user
            )


# customer serializers .2
class CustomerSerializer(serializers.ModelSerializer):
    due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_due"
    )
    surplus = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_surplus"
    )
    groups = CustomerReadOnlyGroupSerializer(read_only=True, source="group")
    employee = ReadOnlyEmployeeSerializer(
        read_only=True, many=True, source="assigned_to"
    )

    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "number",
            "email",
            "address",
            "logo",
            "groups",
            "employee",
            "due",
            "surplus",
        )

    def validate_email(self, value):
        if value == "":
            return None
        return value

    def validate(self, data):
        user = self.context["request"].user
        if user.parent:
            raise ValidationError("You don't have permission to create new customers.")
        return data

    def create(self, validated_data):
        owner = self.context["request"].user
        assigned_to = validated_data.pop("assigned_to", [])

        cusomer = Customer.objects.create(owner=owner, **validated_data)

        return cusomer


# service serializers
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ("id", "name")

    def validate(self, data):
        name = data.get("name")
        owner = self.context["request"].user

        if Service.objects.filter(name__iexact=name, owner=owner).exists():
            raise ValidationError("A service with this name already exists.")
        return data

    def create(self, validated_data):
        owner = self.context["request"].user
        return Service.objects.create(owner=owner, **validated_data)


# record serializers
class RecordSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_amount"
    )
    paid_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_paid_amount"
    )
    due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_due"
    )

    customers = CustomerNestedSerializer(read_only=True, source="customer")
    pay = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Record
        fields = (
            "id",
            "customer",
            "customers",
            "service",
            "pcs",
            "created_at",
            "rate",
            "discount",
            "amount",
            "paid_amount",
            "due",
            "pay",
        )
        read_only_fields = ["id"]

    def validate_created_at(self, value):
        if value > timezone.now():
            raise ValidationError("Record cannot be created in the future.")
        return value

    def validate(self, attrs):
        customer = attrs.get("customer")
        service = attrs.get("service")

        if not attrs.get("rate"):
            exists = GroupRate.objects.filter(
                group=customer.group,
                service=service,
            ).exists()

            if not exists:
                raise ValidationError("No rate defined for this service.")

        return attrs


class UpdateRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = Record
        fields = (
            "id",
            "customer",
            "service",
            "pcs",
            "created_at",
            "rate",
            "discount",
        )
        read_only_fields = ["id"]

    def validate(self, attrs):
        if self.instance and "customer" in attrs:
            if (
                self.instance.customer != attrs["customer"]
                or self.instance.created_at.date() != attrs["created_at"].date()
            ):
                has_transaction = (
                    self.instance.advanceusage_set.exists()
                    or self.instance.allocation_set.exists()
                )
                if has_transaction:
                    raise ValidationError(
                        {
                            "customer": (
                                "Customer or Date cannot be changed after a transaction have been recorded against a work entry."
                            )
                        }
                    )
        return attrs


class RecordNestedSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_amount"
    )
    service = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Record
        fields = ("id", "service", "pcs", "rate", "discount", "amount")
        read_only_fields = fields


# payment serializers
class CloudInaryImageField(serializers.ImageField):

    def to_representation(self, value):
        if not value:
            return None
        return value.url
    




class PaymentSerializer(serializers.ModelSerializer):
    customers = CustomerNestedSerializer(read_only=True, source="customer")
    image= CloudInaryImageField(allow_null= True, required=False)

    class Meta:
        model = Payment
        fields = (
            "id",
            "customer",
            "customers",
            "mode",
            "amount",
            "image",
            "created_at",
        )

    def validate(self, attrs):
        if (attrs.get("mode") == "o"
            and not attrs.get( "image")
            and self.context['request'].user.profile.setting_mode   
        ):
            raise ValidationError(
                {"message": "Image is required for online payments."}
            )
        return attrs
        


class PaymentNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "mode", "amount", "image", "created_at")
        read_only_fields = fields


# advance serializers
class AdvanceLogSerializer(serializers.Serializer):
    customers = CustomerNestedSerializer(read_only=True, source="customer")
    # advance created
    payments = PaymentNestedSerializer(read_only=True, source="payment")
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="advance.total_amount"
    )

    # advance used
    records = RecordNestedSerializer(
        source="advanceusage_set", many=True, read_only=True
    )
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


# audit log serializers
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id", "model", "action", "before", "after", "logged_at", "reason")
        read_only_fields = fields


# request serializers
class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        fields = ("id", "record", "amount", "created_at", "status")
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, data):
        user = self.context["request"].user
        if user.parent is None:
            raise ValidationError("Admin's cannot create requests.")
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        records = validated_data.get("record")

        amount = 0

        for record in records:
            amount += record.amount

        validated_data["amount"] = amount
        return Request.objects.create(owner=user, **validated_data)

    def update(self, instance, validated_data):
        records = validated_data.get("record", instance.record)
        instance.record = records
        amount = 0
        for record in records:
            amount += record.amount
        instance.amount = amount
        instance.save()
        return instance


class AproveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = "id"
        read_only_fields = fields

    def validate(self, data):
        user = self.context["request"].user
        if user.parent:
            raise ValidationError("You don't have permission to aprove requests.")
        return data


class RejectRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ("id", "reason")
        read_only_fields = ["id"]

    def validate(self, data):
        user = self.context["request"].user
        if user.parent:
            raise ValidationError("You don't have permission to reject requests.")
        return data
