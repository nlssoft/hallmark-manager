# cls
from .models import Groups, Customer, Service, GroupRate, Record, Payment, Advance, AdvanceUsage, AuditLog, Request
from .serializers import ReadOnlyGroupSerializer, GroupSerializer, RemoveServiceGroupSerializer, CustomerSerializer, RecordSerializer, \
    ServiceSerializer, RecordSerializer, PaymentSerializer, AdvanceLogSerializer, AuditLogSerializer, RequestSerializer
from  .permissions import ParentAccount, ActionPermission
from .money_logic import PaymentService

#tools
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework import status   
from django.db import transaction
from django.db.models import F, Value, DecimalField, Sum
from django.db.models.functions import Coalesce


class GroupsViewset(ModelViewSet):
    permission_classes = [ParentAccount]

    
    def get_queryset(self):
        return Groups.objects.filter(owner=self.request.user)\
            .select_related('owner').prefetch_related('grouprate_set')
    
    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadOnlyGroupSerializer
        if self.action == 'remove_service':
            return RemoveServiceGroupSerializer
        
        return GroupSerializer
    
    @action(detail=True, methods=['post'], url_path='remove-service')
    def remove_service(self, request, pk=None):
        group = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.validated_data['service']
        
        try:
            group_rate = GroupRate.objects.get(group=group, service=service)
            group_rate.delete()
            return Response({"detail": "Service removed from group successfully."}, status=status.HTTP_200_OK)
        except GroupRate.DoesNotExist:
            return Response({"detail": "Service not found in the specified group."}, status=status.HTTP_404_NOT_FOUND)
        

class CustomerViewset(ModelViewSet):
    permission_classes = [ActionPermission]
    serializer_class = CustomerSerializer

    def get_queryset(self):
        return Customer.objects.filter(owner=self.request.user)\
            .select_related('group').prefetch_related('group__grouprate_set__service',  'assigned_to')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.records.exists() or instance.payments.exists() or instance.advances.exists():
            return Response({"detail": "Cannot delete customer with existing work history."}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceViewset(ModelViewSet):
    permission_classes = [ParentAccount]
    serializer_class = ServiceSerializer

    def get_queryset(self):
        return Service.objects.filter(owner=self.request.user).select_related('owner')
    

class RecordViewset(ModelViewSet):
    permission_classes=[ParentAccount]
    serializer_class= RecordSerializer

    def get_queryset(self):
        return Record.objects.filter(customer__owner= self.request.user)\
            .annotate(
                _amount=F('rate')* F('pcs'))\
                    .annotate(
                        _paid_amount= (
                            Coalesce(
                                Sum('allocation__amount'),
                                Value(0),
                                output_field=DecimalField(),
                            ) + Coalesce(
                                Sum('advanceusage__amount'),
                                Value(0),
                                output_field=DecimalField(),
                            )
                        )
                    ).annotate(_due = F('_amount') - F('_paid_amount') - F('discount'))\
                        .select_related("customer")\
                        .prefetch_related('allocation8', 'advanceusages')
    

    def create(self, request, *args, **kwargs):
        serializer= self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            pay= serializer.pop('pay')
            record = serializer.save()
            PaymentService.advance_allocate(record)
            if pay:
                Payment.objects.create(customer=record.customer, amount=record.amount - record.discount - record-)
 
            return Response(self.get_serializer(record), status=status.HTTP_201_CREATED)
        

    





