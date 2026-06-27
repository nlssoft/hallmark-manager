from user.serializers import ReadOnlyEmployeeSerializer
from .models import (
    Groups,
    Customer,
    Service,
    GroupRate,
    Record,
    Payment,
    Advance,
    AdvanceUsage,
    AuditLog,
    Request,
    SnapShotRequest,
)
from .nestedserializer import NestedCustomerSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from collections import OrderedDict
from decimal import Decimal
from collections import defaultdict
from django.utils import timezone

# group serializers


# Read
class NestedGroupRateSerializer(serializers.Serializer):
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
    group_rate = NestedGroupRateSerializer(
        read_only=True, source="grouprate_set", many=True
    )
    customer = NestedCustomerSerializer(
        read_only=True, many=True, source="customer_set"
    )


class NestedGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(
        max_length=255, allow_blank=True, allow_null=True, required=False
    )  # keep or not keep
    group_rate = NestedGroupRateSerializer(
        read_only=True, source="grouprate_set", many=True
    )


# Write
class WriteGroupSerializer(serializers.Serializer):
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
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            self.fields["service"].queryset = Service.objects.filter(owner=user)
        else:
            self.fields["service"].queryset = Service.objects.none()

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


# Action
class RemoveServiceGroupSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = GroupRate
        fields = ("id", "service")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            self.fields["service"].queryset = Service.objects.filter(owner=user)
        else:
            self.fields["service"].queryset = Service.objects.none()


class sync_customerSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), many=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            self.fields["customer"].queryset = Customer.objects.filter(owner=user)
        else:
            self.fields["customer"].queryset = Customer.objects.none()


# customer serializers .2
# Read & Write
class CustomerSerializer(serializers.ModelSerializer):
    due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_due"
    )
    surplus = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_surplus"
    )
    groups = NestedGroupSerializer(read_only=True, source="group")
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


# Read
class ReadOnlyRecordSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_amount"
    )
    paid_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_paid"
    )
    due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_due"
    )
    customer = NestedCustomerSerializer(read_only=True)
    service = serializers.CharField(source="service.name", read_only=True)

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
            "amount",
            "paid_amount",
            "due",
        )
        read_only_fields = fields


class NestedWithOutCustomerRecordSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_amount"
    )
    paid_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_paid"
    )
    due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_due"
    )
    service = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Record
        fields = (
            "id",
            "service",
            "pcs",
            "created_at",
            "rate",
            "discount",
            "amount",
            "paid_amount",
            "due",
        )
        read_only_fields = fields


class PaymentNestedRecordSerializer(serializers.ModelSerializer):

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    service = serializers.CharField(source="service.name", read_only=True)

    used = serializers.SerializerMethodField()

    class Meta:
        model = Record
        fields = ("id", "service", "pcs", "rate", "discount", "amount", "used")
        read_only_fields = fields

    def get_used(self, record):
        allocated_money_map = self.context.get("allocated_money_map", {})
        return allocated_money_map.get(record.id, Decimal("0.00"))


class ReportRecordSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_amount"
    )
    paid_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_paid"
    )
    due = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source="_due"
    )

    customer_id = serializers.IntegerField(source="customer.pk", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_address = serializers.CharField(source="customer.address", read_only=True)

    service = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Record
        fields = (
            "id",
            "customer_id",
            "customer_name",
            "customer_address",
            "service",
            "pcs",
            "created_at",
            "rate",
            "discount",
            "amount",
            "paid_amount",
            "due",
        )
        read_only_fields = fields


# Write
class CreateRecordSerializer(serializers.ModelSerializer):
    pay = serializers.BooleanField(write_only=True, required=False, default=False)

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

        rate = attrs.get("rate", 0)
        pcs = attrs.get("pcs", 0)
        discount = attrs.get("discount", 0)

        amount = rate * pcs

        if discount > amount:
            raise ValidationError("Discount cannot be greater then amount.")

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

        rate = attrs.get("rate", self.instance.rate)
        pcs = attrs.get("pcs", self.instance.pcs)
        discount = attrs.get("discount", self.instance.discount)

        amount = rate * pcs

        if discount > amount:
            raise ValidationError("Discount cannot be greater then amount.")

        return attrs


# payment serializers


# Helper
class CloudInaryImageField(serializers.ImageField):

    def to_representation(self, value):
        if not value:
            return None
        return value.url


# Read
class ReadOnlyPaymentSerializer(serializers.ModelSerializer):
    customer = NestedCustomerSerializer(read_only=True)
    image = CloudInaryImageField(read_only=True)
    left = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="_left", read_only=True
    )
    records = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id",
            "customer",
            "mode",
            "amount",
            "left",
            "image",
            "created_at",
            "records",
        )

    def get_records(self, payment):
        combined_allocated = defaultdict(Decimal)
        record_by_id = {}

        for a in payment.allocation_set.all():
            combined_allocated[a.record_id] += a.amount
            record_by_id[a.record_id] = a.record

        for a in payment.advance_set.all():
            for au in a.advanceusage_set.all():
                combined_allocated[au.record_id] += au.amount
                record_by_id[au.record_id] = au.record

        return PaymentNestedRecordSerializer(
            list(record_by_id.values()),
            many=True,
            context={**self.context, "allocated_money_map": dict(combined_allocated)},
        ).data


class NestedPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "mode", "amount", "image", "created_at")
        read_only_fields = fields


# write
class WritePaymentSerializer(serializers.ModelSerializer):
    image = CloudInaryImageField(allow_null=True, required=False)

    class Meta:
        model = Payment
        fields = (
            "id",
            "customer",
            "mode",
            "amount",
            "image",
            "created_at",
        )

    def validate_created_at(self, value):
        if value > timezone.now():
            raise ValidationError("Payment cannot be created in the future.")
        return value

    def validate(self, attrs):
        if (
            attrs.get("mode") == "o"
            and not attrs.get("image")
            and self.context["request"].user.profile.setting_mode
        ):
            raise ValidationError({"message": "Image is required for online payments."})
        return attrs


# audit log serializers
class ReadOnlyAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id", "model", "action", "before", "after", "logged_at", "reason")
        read_only_fields = fields


# request serializers


# Read
class ReadOnlyRequestSerializer(serializers.ModelSerializer):

    record = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Request
        fields = ("id", "record", "total_amount", "created_at", "status")
        read_only_fields = fields

    def get_record(self, obj):
        groups = OrderedDict()
        records = obj.record.all()

        if obj.status == "p":

            for record in records:
                if record._due <= Decimal("0.00"):
                    continue

                customer_id = record.customer_id

                if customer_id not in groups:
                    groups[customer_id] = {
                        "customer": NestedCustomerSerializer(record.customer).data,
                        "records": [],
                        "amount": Decimal("0.00"),
                    }

                groups[customer_id]["records"].append(
                    NestedWithOutCustomerRecordSerializer(record).data
                )
                groups[customer_id]["amount"] += Decimal(record._due)

            return [{**g, "amount": str(g["amount"])} for g in groups.values()]

        snapshots = SnapShotRequest.objects.filter(request=obj).select_related(
            "record", "record__customer", "record__service"
        )

        for snapshot in snapshots:
            record = snapshot.record
            customer_id = record.customer_id

            if customer_id not in groups:
                groups[customer_id] = {
                    "customer": NestedCustomerSerializer(record.customer).data,
                    "records": [],
                    "amount": Decimal("0.00"),
                }

            record_data = NestedWithOutCustomerRecordSerializer(record).data
            record_data["requested_amount"] = str(snapshot.due_amount)

            groups[customer_id]["records"].append(record_data)

            groups[customer_id]["amount"] += snapshot.due_amount

        return [{**g, "amount": str(g["amount"])} for g in groups.values()]

    def get_total_amount(self, obj):
        if obj.status == "p":
            return str(
                sum(r._due for r in obj.record.all() if r._due > Decimal("0.00"))
            )

        return str(
            sum(r.due_amount for r in SnapShotRequest.objects.filter(request=obj))
        )


# Write
class WriteRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        fields = ("id", "record")
        read_only_fields = ["id"]

    # here records are just a convinet name for value
    def validate_record(self, records):

        user = self.context["request"].user

        pending = (
            Request.objects.filter(
                status="p",
                owner=user,
                record__in=records,
            )
            .values_list("record", flat=True)
            .distinct()
        )

        # on update exclude your own request
        if self.instance:
            pending = pending.exclude(pk=self.instance.pk)

        if pending.exists():
            raise ValidationError("One or more records already have a pending request.")

        if not records:
            raise ValidationError("Select at least one record.")

        return records

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            fields["record"].child_relation.queryset = Record.objects.none()
            return fields

        pending_record_ids = (
            Request.objects.filter(status="p", owner=request.user, record__isnull=False)
            .values_list("record", flat=True)
            .distinct()
        )
        if self.instance:
            pending_record_ids = pending_record_ids.exclude(pk=self.instance.pk)

        if user.parent_id is not None:
            fields["record"].child_relation.queryset = (
                Record.objects.with_financials()
                .filter(customer__assigned_to=request.user)
                .select_related("customer", "service")
                .prefetch_related("advanceusage_set", "allocation_set")
                .filter(_due__gt=0)
                .exclude(pk__in=pending_record_ids)
            )

        return fields


"""
# need to think about


class NestedRecordSerializer(serializers.ModelSerializer):

    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    service = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = Record
        fields = ("id", "service", "pcs", "rate", "discount", "amount")
        read_only_fields = fields


# Advance Usage nested serializer
class NestedAdvanceUsageSerializer(serializers.ModelSerializer):
    record = NestedRecordSerializer()

    class Meta:
        model = AdvanceUsage
        fields = ["record", "amount", "created_at"]



class ReadOnlyAdvanceLogSerializer(serializers.ModelSerializer):
    customer = NestedCustomerSerializer(read_only=True)
    # advance created
    payment = NestedPaymentSerializer(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    left = serializers.DecimalField(
        max_digits=10, decimal_places=2, source="_left", read_only=True
    )

    # advance used
    usage = NestedAdvanceUsageSerializer(
        many=True, read_only=True, source="advanceusage_set"
    )

    class Meta:
        model = Advance
        fields = ["customer", "payment", "total_amount", "created_at", "usage", "left"]


"""
