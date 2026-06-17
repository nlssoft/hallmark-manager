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
    SnapShotRequest,
)
from .serializers import (
    ReadOnlyGroupSerializer,
    WriteGroupSerializer,
    RemoveServiceGroupSerializer,
    CustomerSerializer,
    ReadOnlyRecordSerializer,
    CreateRecordSerializer,
    UpdateRecordSerializer,
    ServiceSerializer,
    CreateRecordSerializer,
    ReadOnlyPaymentSerializer,
    WritePaymentSerializer,
    ReadOnlyAdvanceLogSerializer,
    ReadOnlyAuditLogSerializer,
    ReadOnlyRequestSerializer,
    WriteRequestSerializer,
    sync_customerSerializer,
)
from .permissions import (
    ParentAccount_Only,
    CustomerEndpointPermission,
    RecordEndpointPermission,
    RequestEndpointPermission,
)
from .money_logic import PaymentService
from .requestservices import RequestService
from .services.helper_functions import get_reason
from .paginations import StandardPagination, LargePagination
from .filters import (
    RecordFilter,
    PaymentFilter,
    AdvanceLogFilter,
    AuditLogFilter,
    RequestFilter,
)

# tools
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
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
    Prefetch,
)
from django.db.models.functions import Coalesce


class GroupsViewset(ModelViewSet):
    permission_classes = [ParentAccount_Only]
    pagination_class = StandardPagination
    filter_backends = [SearchFilter]
    search_fields = ["name", "customer__name"]

    queryset = Groups.objects.none()

    def get_queryset(self):
        return (
            Groups.objects.filter(owner=self.request.user)
            .select_related("owner")
            .prefetch_related("grouprate_set", "grouprate_set__service", "customer_set")
            .order_by("-pk")
            .distinct()
        )

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadOnlyGroupSerializer
        if self.action == "remove_service":
            return RemoveServiceGroupSerializer
        if self.action == "sync_customer":
            return sync_customerSerializer

        return WriteGroupSerializer

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
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "logo"]
    ordering_fields = ["_due", "_surplus"]
    ordering = ["name"]

    serializer_class = CustomerSerializer
    queryset = Customer.objects.none()

    def get_queryset(self):

        base = Customer.objects.filter(owner=self.request.user)
        if self.request and self.request.user.parent_id is not None:
            base = Customer.objects.filter(assigned_to=self.request.user)

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
            .select_related(
                "group",
            )
            .prefetch_related("assigned_to", "group__grouprate_set__service")
            .order_by("-pk")
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if (
            instance.record_set.exists()
            or instance.payment_set.exists()
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
    pagination_class = StandardPagination
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    serializer_class = ServiceSerializer
    queryset = Service.objects.none()

    def get_queryset(self):
        return Service.objects.filter(owner=self.request.user).select_related("owner")


class RecordViewset(ModelViewSet):
    permission_classes = [RecordEndpointPermission]
    pagination_class = LargePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RecordFilter
    search_fields = ["customer__name", "customer__logo"]
    ordering_fields = ["_due"]
    ordering = ["-created_at", "-pk"]

    queryset = Record.objects.none()

    def get_queryset(self):

        base = Record.objects.with_financials().filter(
            customer__owner=self.request.user
        )

        if self.request and self.request.user.parent_id is not None:
            base = Record.objects.with_financials().filter(
                customer__assigned_to=self.request.user
            )

        return base.select_related("customer", "service").prefetch_related(
            "allocation_set",
            "advanceusage_set",
        )

    def get_serializer_class(self):
        if self.action in ["create"]:
            return CreateRecordSerializer

        if self.action in ["update", "partial_update"]:
            return UpdateRecordSerializer

        return ReadOnlyRecordSerializer

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
                PaymentService.allocate_selected(record)

            return Response(
                self.get_serializer(record).data, status=status.HTTP_201_CREATED
            )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        record = self.get_object()
        before = dict(ReadOnlyRecordSerializer(record).data)
        reason = get_reason(request)

        PaymentService.record_rollback(record)
        response = super().update(request, *args, **kwargs)
        PaymentService.re_balance(record.customer)
        after = dict(
            ReadOnlyRecordSerializer(self.get_queryset().get(pk=record.pk)).data
        )

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
        before = dict(ReadOnlyRecordSerializer(record).data)

        reason = get_reason(request)

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

    @action(detail=False, methods=["get"])
    def requestable(self, request, pk=None):
        queryset = (
            self.get_queryset()
            .filter(_due__gt=0)
            .exclude(
                pk__in=Request.objects.filter(
                    status="p",
                    owner=request.user,
                )
                .values_list("record", flat=True)
                .order_by("-created_at", "-pk")
            )
        )

        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentViewset(ModelViewSet):
    permission_classes = [ParentAccount_Only]
    pagination_class = LargePagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = PaymentFilter
    search_fields = ["customer__name", "customer__logo"]

    queryset = Payment.objects.none()

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadOnlyPaymentSerializer
        return WritePaymentSerializer

    def get_queryset(self):
        return (
            Payment.objects.filter(customer__owner=self.request.user)
            .select_related("customer")
            .order_by("-created_at", "-pk")
        )

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
        before = dict(ReadOnlyPaymentSerializer(payment).data)
        reason = get_reason(request)

        allocation_record, advanceusage_record = PaymentService.Payment_rollback(
            payment
        )

        response = super().update(request, *args, **kwargs)

        # to refresh state
        payment.refresh_from_db()
        PaymentService.update_allocate(payment, allocation_record, advanceusage_record)
        after = dict(
            ReadOnlyPaymentSerializer(self.get_queryset().get(pk=payment.pk)).data
        )

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
        before = dict(ReadOnlyPaymentSerializer(payment).data)
        reason = get_reason(request)

        AuditLog.objects.create(
            model="p", user=request.user, before=before, action="d", reason=reason
        )
        return super().destroy(request, *args, **kwargs)


class AdvanceLogViewset(ReadOnlyModelViewSet):
    permission_classes = [ParentAccount_Only]
    pagination_class = LargePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AdvanceLogFilter
    search_fields = ["customer__name", "customer__logo"]
    ordering_fields = ["_left", "total_amount", "created_at"]

    serializer_class = ReadOnlyAdvanceLogSerializer
    queryset = Advance.objects.none()

    def get_queryset(self):
        return (
            Advance.objects.filter(customer__owner=self.request.user)
            .annotate(
                _left=F("total_amount")
                - Coalesce(
                    Sum("advanceusage__amount"), Value(0), output_field=DecimalField()
                )
            )
            .select_related("customer", "payment")
            .prefetch_related(
                Prefetch(
                    "advanceusage_set",
                    queryset=AdvanceUsage.objects.select_related("record"),
                ),
            )
        ).order_by("-pk")


class AuditLogViewset(ReadOnlyModelViewSet):
    permission_classes = [ParentAccount_Only]
    pagination_class = LargePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ["before__customer__name", "before__customer__logo"]
    ordering_fields = ["logged_at"]

    serializer_class = ReadOnlyAuditLogSerializer
    queryset = AuditLog.objects.none()

    def get_queryset(self):
        return AuditLog.objects.filter(user=self.request.user).order_by("-pk")


class RequestViewset(ModelViewSet):
    permission_classes = [RequestEndpointPermission]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RequestFilter
    search_fields = ["owner__username"]
    ordering_fields = ["created_at"]

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in SAFE_METHODS:
            return ReadOnlyRequestSerializer

        return WriteRequestSerializer

    def get_queryset(self):
        record_qs = (
            Record.objects.select_related("customer", "service")
            .annotate(
                _amount=ExpressionWrapper(
                    F("rate") * F("pcs"), output_field=DecimalField()
                )
            )
            .annotate(
                _paid=Coalesce(
                    Sum("allocation__amount"), Value(0), output_field=DecimalField()
                )
                + Coalesce(
                    Sum("advanceusage__amount"), Value(0), output_field=DecimalField()
                )
            )
            .annotate(
                _due=F("_amount")
                - F("_paid")
                - Coalesce(F("discount"), Value(0), output_field=DecimalField())
            )
        )

        if self.request and self.request.user.parent_id is None:
            return (
                Request.objects.filter(owner__parent=self.request.user)
                .prefetch_related(
                    Prefetch("record", queryset=record_qs),
                    "record",
                    "record__customer",
                    "record__service",
                )
                .order_by("-created_at", "-pk")
            )
        else:
            return (
                Request.objects.filter(owner=self.request.user)
                .prefetch_related(
                    Prefetch("record", queryset=record_qs),
                    "record",
                    "record__customer",
                    "record__service",
                )
                .order_by("-created_at", "-pk")
            )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @transaction.atomic()
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        obj = self.get_object()

        RequestService.prune(obj)
        records = obj.record.all().with_financials()

        snapshotrequest = [
            SnapShotRequest(request=obj, record=r, due_amount=r._due) for r in records
        ]

        SnapShotRequest.objects.bulk_create(snapshotrequest)

        PaymentService.allocate_selected_many(records)
        obj.status = "a"
        obj.save(update_fields=["status"])

        return Response(status=status.HTTP_200_OK)

    @transaction.atomic()
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        obj = self.get_object()
        RequestService.prune(obj)

        records = obj.record.all()

        reason = get_reason(request)

        snapshotrequest = [
            SnapShotRequest(request=obj, record=r, due_amount=r._due) for r in records
        ]

        SnapShotRequest.objects.bulk_create(snapshotrequest)

        obj.reason = reason
        obj.status = "r"
        obj.save(update_fields=["reason", "status"])

        return Response(status=status.HTTP_200_OK)
