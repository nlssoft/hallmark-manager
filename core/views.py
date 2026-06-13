# cls
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
)
from .serializers import (
    ReadOnlyGroupSerializer,
    GroupSerializer,
    RemoveServiceGroupSerializer,
    CustomerSerializer,
    RecordSerializer,
    UpdateRecordSerializer,
    ServiceSerializer,
    RecordSerializer,
    PaymentSerializer,
    AdvanceLogSerializer,
    AuditLogSerializer,
    RequestSerializer,
    AproveRequestSerializer,
    RejectRequestSerializer,
    sync_customerSerializer,
)
from .permissions import (
    ParentAccount_Only,
    CustomerEndpointPermission,
    RequestEndpointPermission,
)
from .money_logic import PaymentService
from .services.helper_functions import get_reason

# tools
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import (
    F,
    Value,
    DecimalField,
    Sum,
    ExpressionWrapper,
    Case,
    When,
    OuterRef,
    Subquery,
    Q,
)
from django.db.models.functions import Coalesce


class GroupsViewset(ModelViewSet):
    permission_classes = [ParentAccount_Only]
    queryset = Groups.objects.none()

    def get_queryset(self):
        return (
            Groups.objects.filter(owner=self.request.user)
            .select_related("owner")
            .prefetch_related("grouprate_set")
        )

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadOnlyGroupSerializer
        if self.action == "remove_service":
            return RemoveServiceGroupSerializer
        if self.action == "sync_customer":
            return sync_customerSerializer

        return GroupSerializer

    @action(detail=True, methods=["post"], url_path="remove-service")
    def remove_service(self, request, pk=None):
        group = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.validated_data["service"]

        try:
            group_rate = GroupRate.objects.get(group=group, service=service)
            group_rate.delete()
            return Response(
                {"detail": "Service removed from group successfully."},
                status=status.HTTP_200_OK,
            )
        except GroupRate.DoesNotExist:
            return Response(
                {"detail": "Service not found in the specified group."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["post"], url_path="sync-members")
    def sync_customer(self, request, pk=None):
        group = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_id = {customer.id for customer in serializer.validated_data["customer"]}

        Customer.objects.filter(group=group).exclude(id__in=new_id).update(group=None)

        Customer.objects.filter(owner=request.user, id__in=new_id).exclude(
            group=group
        ).update(group=group)

        return Response({"synced": len(new_id)})


class CustomerViewset(ModelViewSet):
    permission_classes = [CustomerEndpointPermission]
    serializer_class = CustomerSerializer
    queryset = Customer.objects.none()

    def get_queryset(self):

        user = self.request.user

        if user.parent:
            base = Customer.objects.filter(assigned_to=user)
        else:
            base = Customer.objects.filter(owner=user)

        record_total = (
            Record.objects.filter(customer_id=OuterRef("pk"))
            .values("customer_id")
            .annotate(
                total=Coalesce(
                    Sum(
                        ExpressionWrapper(
                            F("rate") * F("pcs")
                            - Coalesce(
                                F("discount"), Value(0), output_field=DecimalField()
                            ),
                            output_field=DecimalField(),
                        )
                    ),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
            .values("total")
        )

        payment_total = (
            Payment.objects.filter(customer_id=OuterRef("pk"))
            .values("customer_id")
            .annotate(
                total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
            )
            .values("total")
        )

        return (
            base.annotate(
                _record_total=Coalesce(
                    Subquery(record_total, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
                _payment_total=Coalesce(
                    Subquery(payment_total, output_field=DecimalField()),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
            .annotate(_balance=F("_record_total") - F("_payment_total"))
            .annotate(
                _due=Case(
                    When(_balance__gt=0, then=F("_balance")),
                    default=Value(0),
                    output_field=DecimalField(),
                ),
                _surplus=Case(
                    When(_balance__lt=0, then=-F("_balance")),
                    default=Value(0),
                    output_field=DecimalField(),
                ),
            )
            .select_related("group")
            .prefetch_related("assigned_to")
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            instance.records.exists()
            or instance.payments.exists()
            or instance.advances.exists()
        ):
            return Response(
                {"detail": "Cannot delete customer with existing work history."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceViewset(ModelViewSet):
    permission_classes = [ParentAccount_Only]
    serializer_class = ServiceSerializer
    queryset = Service.objects.none()

    def get_queryset(self):
        return Service.objects.filter(owner=self.request.user).select_related("owner")


class RecordViewset(ModelViewSet):
    permission_classes = [ParentAccount_Only]
    serializer_class = RecordSerializer
    queryset = Record.objects.none()

    def get_queryset(self):
        return (
            Record.objects.filter(customer__owner=self.request.user)
            .annotate(
                _amount=ExpressionWrapper(
                    F("rate") * F("pcs"), output_field=DecimalField()
                )
            )
            .annotate(
                _paid_amount=(
                    Coalesce(
                        Sum("allocation__amount"),
                        Value(0),
                        output_field=DecimalField(),
                    )
                    + Coalesce(
                        Sum("advanceusage__amount"),
                        Value(0),
                        output_field=DecimalField(),
                    )
                )
            )
            .annotate(
                _due=(
                    F("_amount")
                    - F("_paid_amount")
                    - Coalesce(F("discount"), Value(0), output_field=DecimalField())
                )
            )
            .select_related("customer", "service")
            .prefetch_related("allocation_set", "advanceusage_set")
        )

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return UpdateRecordSerializer

        return RecordSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            pay = serializer.validated_data.pop("pay")
            record = serializer.save()
            PaymentService.advance_allocate(record)
            if pay:
                # send as a list after refetching
                record = self.get_queryset().get(pk=record.pk)
                PaymentService.allocate_selected([record])

            return Response(
                self.get_serializer(record).data, status=status.HTTP_201_CREATED
            )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        record = self.get_object()
        before = dict(RecordSerializer(record).data)
        reason, error = get_reason(request)

        if error:
            return error

        PaymentService.record_rollback(record)
        response = super().update(request, *args, **kwargs)
        PaymentService.re_balance(record.customer)
        after = dict(RecordSerializer(self.get_queryset().get(pk=record.pk)).data)

        AuditLog.objects.create(
            model="r",
            user=request.user,
            before=before,
            after=after,
            action="u",
            reason=reason,
        )

        return response

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        customer = record.customer
        before = dict(RecordSerializer(record).data)

        reason, error = get_reason(request)

        if error:
            return error

        with transaction.atomic():
            record.delete()
            PaymentService.re_balance(customer)

            AuditLog.objects.create(
                model="r",
                user=request.user,
                before=before,
                action="d",
                reason=reason,
            )

            return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentViewset(ModelViewSet):
    permission_classes = [ParentAccount_Only]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.none()

    def get_queryset(self):
        return Payment.objects.filter(customer__owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            payment = serializer.save()
            PaymentService.allocate(payment)

            return Response(
                self.get_serializer(payment).data, status=status.HTTP_201_CREATED
            )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        payment = self.get_object()
        before = dict(PaymentSerializer(payment).data)
        reason, error = get_reason(request)

        if error:
            return error

        PaymentService.Payment_rollback(payment)

        response = super().update(request, *args, **kwargs)

        # to refresh state
        payment.refresh_from_db()
        PaymentService.allocate(payment)
        after = dict(PaymentSerializer(self.get_queryset().get(pk=payment.pk)).data)

        AuditLog.objects.create(
            model="p",
            user=request.user,
            before=before,
            after=after,
            action="u",
            reason=reason,
        )

        return response

    def destroy(self, request, *args, **kwargs):
        payment = self.get_object()
        before = dict(PaymentSerializer(payment).data)
        reason, error = get_reason(request)

        if error:
            return error

        AuditLog.objects.create(
            model="p", user=request.user, before=before, action="d", reason=reason
        )
        return super().destroy(request, *args, **kwargs)


class AdvanceLogViewset(ReadOnlyModelViewSet):
    permission_classes = [ParentAccount_Only]
    serializer_class = AdvanceLogSerializer
    queryset = Advance.objects.none()

    def get_queryset(self):
        user = self.request.user
        return (
            Advance.objects.filter(customer__owner=user)
            .select_related("customer", "payment")
            .prefetch_related("advanceusage_set", "advanceusage_set__record")
        )


class AuditLogViewset(ReadOnlyModelViewSet):
    permission_classes = [ParentAccount_Only]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.none()

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user)


class RequestViewset(ModelViewSet):
    permission_classes = [RequestEndpointPermission]

    def get_serializer(self, *args, **kwargs):
        if self.action == "approve":
            return AproveRequestSerializer
        if self.action == "reject":
            return RejectRequestSerializer

        return RequestSerializer
