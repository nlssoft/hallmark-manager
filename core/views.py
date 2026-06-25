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
    Allocation,
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
    ReportRecordSerializer,
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
from .services.helper_functions import get_reason, get_customer_ids, get_date_range, get_employee_id, get_include_header
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
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
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
    Count,
)
from django.db.models.functions import Coalesce


class GroupsViewset(ModelViewSet):
    permission_classes = [ParentAccount_Only]
    pagination_class = StandardPagination
    filter_backends = [SearchFilter]
    search_fields = ["name", "customer__name"]


    def get_queryset(self):
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Groups.objects.none()
        
        return (
            Groups.objects.filter(owner=user)
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


    def get_queryset(self):
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Customer.objects.none()


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
            Customer.objects.filter(Q(owner=user) | Q(assigned_to=user) ).annotate(
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


    def get_queryset(self):
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Service.objects.none()
        
        return Service.objects.filter(owner=user).select_related("owner")


class RecordViewset(ModelViewSet):
    permission_classes = [RecordEndpointPermission]
    pagination_class = LargePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = RecordFilter
    search_fields = ["customer__name", "customer__logo"]
    ordering_fields = ["_due"]
    ordering = ["-created_at", "-pk"]



    def get_queryset(self):
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Record.objects.none()
        

        base = Record.objects.with_financials().filter(
            Q(customer__owner=user) | Q( customer__assigned_to=user)
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

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return ReadOnlyPaymentSerializer
        return WritePaymentSerializer

    def get_queryset(self):

        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Payment.objects.none()

        return (
            Payment.objects.filter(customer__owner=user)
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


    def get_queryset(self):
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Advance.objects.none()
        
        return (
            Advance.objects.filter(customer__owner=user)
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
    

    def get_queryset(self):
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return AuditLog.objects.none()
    
        return AuditLog.objects.filter(user=user).order_by("-pk")


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
        user = getattr(self.request, "user", None)

        if getattr(self, "swagger_fake_view", False) or not user or not user.is_authenticated:
            return Request.objects.none()
    
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

        return (
            Request.objects.filter(Q(owner__parent=user) | Q(owner=user))
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

# from here summary endpoints 

class RecordSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        separate = request.query_params.get('separate', 'false') == 'true'

        report_type = request.query_params.get('type', 'all')
        employee_ids = get_employee_id(request)
        customer_ids = get_customer_ids(request)
        date_from, date_to = get_date_range(request)

        # queryset subquery
        allocation_total = Allocation.objects.filter(
            record=OuterRef("pk")
        ).values("record").annotate(
            total=Sum("amount")
        ).values("total")

        advance_total = AdvanceUsage.objects.filter(
            record=OuterRef("pk")
        ).values("record").annotate(
            total=Sum("amount")
        ).values("total") 

        qs = (
            Record.objects.filter(
                Q(customer__owner=request.user)
                | Q(customer__assigned_to=request.user)
            )
            .annotate(
                _paid=
                    Coalesce(
                        Subquery(allocation_total),
                        Value(0),
                        output_field=DecimalField(),
                    )
                    +
                    Coalesce(
                        Subquery(advance_total),
                        Value(0),
                        output_field=DecimalField(),
                    ),
                _amount=ExpressionWrapper(
                    F("rate") * F("pcs"),
                    output_field=DecimalField(),
                ),
            )
            .annotate(
                _due=F("_amount")
                - F("_paid")
                - Coalesce(
                    F("discount"),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
        )


        if employee_ids is not None:
            qs = qs.filter(customer__assigned_to__pk__in=employee_ids).distinct()

        if customer_ids is not None:
            qs = qs.filter(customer__in= customer_ids)
        if date_from is not None:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to is not None:
            qs = qs.filter(created_at__date__lte=date_to)

        
        if report_type == 'unpaid':
            qs= qs.filter(_due__gt=0)
        if report_type == 'paid':
            qs= qs.filter(_due__lte=0)


        #company info
        company_info= get_include_header(request)



        # rows 
        rows = ReportRecordSerializer(
                qs.select_related('customer', 'service'),
                many=True
            ).data




        if separate:

            record_totals= list(
                qs.values('customer__pk', 'customer__name')
                .annotate(
                    count= Count('pk'),
                    total_amount= Sum('_amount'),
                    total_discount= Sum('discount'),
                    total_paid=Sum('_paid'),
                    total_due= Sum('_due'),
                            
            ))
        
            service_totals= list(
                qs.values('customer__pk', 'customer__name', 'service__pk', 'service__name')
                .annotate(
                    total_pcs= Sum('pcs'),
                    total_service_amount= Sum('_amount'),
                    total_service_paid= Sum('_paid'),
                    total_service_due= Sum('_due'),
                    )
                )

            customers = {}

            for t in record_totals:
                cid = t["customer__pk"]

                customers[cid] = {
                    'customer_id': cid,
                    'customer_name': t['customer__name'],
                    'totals': {
                        "count": t["count"],
                        "total_amount": t["total_amount"], 
                        "total_discount": t['total_discount'], 
                        "total_paid": t["total_paid"],
                        "total_due": t["total_due"],
                    },
                    'service_totals': [],
                    'records': [],
                }


            for st in service_totals:
                cid= st['customer__pk']

                customers[cid]['service_totals'].append({
                    'service_id': st["service__pk"],
                    "service_name": st['service__name'],
                    "total_pcs": st['total_pcs'],
                    "total_service_amount": st["total_service_amount"],
                    "total_service_paid": st["total_service_paid"],
                    "total_service_due": st["total_service_due"]
                })

            for row in rows:
                cid= row["customer_id"]
                customers[cid]['records'].append(row) 
            
            return Response(
                {
                    "header": company_info,
                    "customers": list(customers.values())
                },
                status=status.HTTP_200_OK,
            )

        else:
            service_totals= list(qs.values('service__pk', 'service__name').annotate(
                total_pcs= Sum('pcs'),
                total_service_amount= Sum('_amount'),
                total_service_paid= Sum('_paid'),
                total_service_due= Sum('_due'),
            ))

            record_totals= qs.aggregate(
                count= Count('id'),
                total_amount= Sum('_amount'),
                total_discount= Sum('discount'),
                total_paid=Sum('_paid'),
                total_due= Sum('_due'),
                
            )

        
        return Response({
            "header": company_info,
            "service_totals": service_totals,
            "records": rows,
            'totals': record_totals
        })


class PaymentSummaryView(APIView):
    permission_classes= [IsAuthenticated]

    def get(self, request):

        separate = request.query_params.get('separate', 'false') == 'true'

        report_type = request.query_params.get('type', 'all')
        employee_ids = get_employee_id(request)
        customer_ids = get_customer_ids(request)
        date_from, date_to = get_date_range(request)

        qs = Payment.objects.filter(Q(customer__owner=self.user) | Q(customer__assigned_to=self.user))


        if employee_ids is not None:
            qs = qs.filter(customer__assigned_to__pk__in=employee_ids).distinct()

        if customer_ids is not None:
            qs = qs.filter(customer__in= customer_ids)
        if date_from is not None:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to is not None:
            qs = qs.filter(created_at__date__lte=date_to)

        
        if report_type == 'by_record':
            
            record_allocation = Record.objects.filter(allocation__payment=OuterRef('pk')).values('record', 'allocation__amount')
            advance_allocation = Record.objects.filter()

            allocation_record_ids= list(Allocation.objects.filter(payment=).values('record_id'))
            advanceusage_record_ids = list(AdvanceUsage.objects.filter(advance__payment=OuterRef('pk')).values('record_id'))

            Record

            qs= qs.annotate(
                
            )



        #company info
        company_info= get_include_header(request)









