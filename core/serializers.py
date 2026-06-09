from user.serializers import ReadOnlyEmployeeSerializer
from .models import  Groups, Customer, Service, GroupRate, \
    Record, Payment, Advance, AdvanceUsage, AuditLog, Request
from user.models import Employee
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# group serializers
class GroupRateNestedSerializer(serializers.Serializer):
    service_id= serializers.IntegerField(source='service.id')
    service_name = serializers.CharField(source='service.name')
    service_rate = serializers.DecimalField(source='rate', max_digits=10, decimal_places=2)


class ReadOnlyGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255, allow_blank=True, allow_null=True, required=False) # keep or not keep
    services = GroupRateNestedSerializer(read_only=True, source='grouprate_set', many=True)


class GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=255, allow_blank=True, allow_null=True, required=False) # keep or not keep
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False, allow_null=True,)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["service"].queryset = Service.objects.filter(owner=request.user)

    def create(self, validated_data):
        owner= self.context["request"].user
        service = validated_data.pop('service')
        rate = validated_data.pop('rate')
        group = Groups.objects.create(**validated_data, owner=owner)
        GroupRate.objects.create(group=group, service=service, rate=rate)
        return group
    
    def update(self, instance, validated_data):
        instance.name= validated_data.get('name', instance.name)
        instance.description= validated_data.get('description', instance.description)
        instance.save()

        service = validated_data.get('service')
        rate = validated_data.get('rate')

        if service is not None and rate is not None:

            GroupRate.objects.update_or_create(
                group=instance, 
                service=service, 
                defaults={'rate': rate}
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

# customer serializers
class CustomerSerializer(serializers.ModelSerializer):
    due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='due_amount')
    surplus = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='surplus_amount')
    groups= ReadOnlyGroupSerializer(read_only=True, source='group')
    employees = ReadOnlyEmployeeSerializer(read_only=True, many= True, source='assigned_to')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if not request:
            return
        
        self.fields["group"].queryset = Groups.objects.filter(owner=request.user)
        
        
        self.fields["assigned_to"].child_relation\
            .queryset = Employee.objects.filter(parent=request.user)


    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "number",
            "email",
            "address",
            "logo",
            "group",
            'groups',
            "assigned_to",
            'employees',
            'due',
            'surplus',
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
        return Customer.objects.create(owner=owner, **validated_data)

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
    
# service serializers
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ("id", "name")

    
    def validate(self, data):
        name= data.get("name")
        owner = self.context["request"].user

        if Service.objects.filter(name__iexact=name, owner=owner).exists():
            raise ValidationError("A service with this name already exists.")
        return data

    def create(self, validated_data):
        owner = self.context["request"].user
        return Service.objects.create(owner=owner, **validated_data)


# record serializers
class RecordSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='_amount')
    paid_amount= serializers.DecimalField(max_digits=10, decimal_places=2, source='_paid_amount')
    due= serializers.DecimalField(max_digits=10, decimal_places=2, source='_due')

    customers = CustomerNestedSerializer(read_only=True)
    pay= serializers.BooleanField(write_only=True, required=False, default=False)

    
    class Meta:
        model = Record
        fields = ("id", 
                  "customer", 
                  'customers', 
                  "service", 
                  "pcs", 
                  "created_at", 
                  "rate", 
                  "discount", 
                  "amount", 
                  "paid_amount", 
                  "due", 
                  "pay")
        read_only_fields = ['id', 'amount', 'paid_amount', 'due']
        

class RecordNestedSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='_amount')
    service = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Record
        fields = ("id", "service", "pcs", "rate", "discount", "amount")
        read_only_fields = fields

# payment serializers
class PaymentSerializer(serializers.ModelSerializer):
    customers= CustomerNestedSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ("id", "customer", 'customers', "mode","amount", "image", "created_at")

class PaymentNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "mode","amount", "image", "created_at")
        read_only_fields = fields

# advance serializers
class AdvanceLogSerializer(serializers.Serializer):
    customers = CustomerNestedSerializer(read_only=True)
    # advance created
    payments = PaymentNestedSerializer(read_only=True)
    total_amount= serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='advance.total_amount')

    # advance used
    records = RecordNestedSerializer(source='advanceusage_set', many=True, read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

# audit log serializers
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ("id", "model", "action", 'before', 'after', "logged_at", 'reason')
        read_only_fields = fields

# request serializers
class RequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        fields = ("id", "record", "amount", "created_at", 'status')
        read_only_fields = ['id', 'status', 'created_at']

    def validate(self, data):
        user = self.context["request"].user
        if user.parent is None:
            raise ValidationError("Admin's cannot create requests.")
        return data
    
    def create(self, validated_data):
        user = self.context["request"].user
        records= validated_data.get("record")

        amount = 0

        for record in records:
            amount += record.amount

        validated_data["amount"] = amount
        return Request.objects.create(owner=user, **validated_data)

    def update(self, instance, validated_data):
        records= validated_data.get("record", instance.record)
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
        fields = ("id")
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
        read_only_fields = ['id']
       

    def validate(self, data):
        user = self.context["request"].user
        if user.parent:
            raise ValidationError("You don't have permission to reject requests.")
        return data
    
