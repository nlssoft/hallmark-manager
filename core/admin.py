from django.contrib import admin
from django.forms.models import ModelForm
from django.http import HttpRequest
from .models import (
    Groups,
    Customer,
    Service,
    GroupRate,
    Record,
    Payment,
    Allocation,
    Advance,
    AdvanceUsage,
    AuditLog,
    Request,
)

from .custome_views import ReadOnlyModelAdmin
from .form import RecordAdminForm, PaymentAdminForm
from .json_serializer import serializer_inst
from .service import PaymentService

from django.db import transaction
from django.db.models import Sum, DecimalField, Value
from django.db.models.functions import Coalesce


@admin.register(Groups)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        "owner",
        "name",
        "description",
    ]

    search_fields = [
        "owner__username",
        "name",
        "description",
    ]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "owner",
        "logo",
        "name",
        "number",
        "email",
        "address",
        "assigned_to",
        "group",
        'due',
        'surplus'
    ]
    search_fields = [
        "owner__username",
        "logo",
        "name",
    ]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "owner",
        "name",
    ]
    search_fields = [
        "owner__username",
        "name",
    ]


@admin.register(GroupRate)
class GroupRateAdmin(admin.ModelAdmin):
    list_display = [
        "group__name",
        "group__description",
        "service",
        "rate",
    ]

    search_fields = ["group__name"]

    list_filter = [
        "service",
        "rate",
    ]


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    form = RecordAdminForm

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _paid_amount=(
                    Coalesce(
                        Sum("allocation__amount"),
                        Value(0),
                        output_field=DecimalField(),
                    )
                    +
                    Coalesce(
                        Sum("advanceusage__amount"),
                        Value(0),
                        output_field=DecimalField(),
                    )
                )
            )
            .select_related("customer", "service")
        )

    # derived methods
    def get_amount(self, obj):
        return obj.amount

    def get_paid(self, obj):
        return obj._paid_amount

    def get_due(self, obj):
        return obj.amount - ((obj._paid_amount or 0) + (obj.discount or 0))

    # methods

    def save_model(self, request, obj, form, change):
        before_obj= Record.objects.get(pk=obj.pk)
        before= serializer_inst(before_obj)
        super().save_model(request, obj, form, change)
        if not change:
            PaymentService.advance_allocate(obj)
        else:
            affected_payments= list(
                Payment.objects.filter(allocation__record=obj).distinct()
            )
            AdvanceUsage.objects.filter(record=obj).delete()
            for payment in affected_payments:
                PaymentService.rollback_plus_allocate(payment)

            PaymentService.advance_allocate(obj)
            after = serializer_inst(obj)
            reason = form.cleaned_data.get('reason')
            AuditLog.objects.create(
                user=obj.customer.owner,
                before=before,
                after=after,
                model='r',
                action='u',                
                reason=reason,
            )

    def delete_model(self, request: HttpRequest, obj: any) -> None:
        with transaction.atomic():
            affected_payments = list(
                Payment.objects.filter(allocation__record=obj).distinct()
            )
            obj.delete()
            
            for payment in affected_payments:
                PaymentService.rollback_plus_allocate(payment)

    def delete_queryset(self, request, queryset):
        with transaction.atomic():
            affected_payments = list(
                Payment.objects.filter(allocation__record__in=queryset).distinct()
            )
            queryset.delete()

            for payment in affected_payments:
                PaymentService.rollback_plus_allocate(payment)

    list_display = [
        "customer__name",
        "customer__address",
        "service",
        "pcs",
        "rate",
        "created_at",
        "get_amount",
        "discount",
        "get_paid",
        "get_due",
    ]

    search_fields = [
        "customer__logo",
        "customer__name",
    ]

    list_filter = [
        "created_at",
    ]

    get_amount.short_description = "Amount"
    get_paid.short_description = "Paid Amount"
    get_due.short_description = "Due"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    form = PaymentAdminForm

    list_display = [
        "customer__name",
        "customer__address",
        "amount",
        "created_at",
        "mode",
        "image",
    ]

    search_fields = [
        "customer__logo",
        "customer__name",
    ]

    list_filter = [
        "created_at",
        "mode",
    ]

    # methods
    def save_model(
        self, request: HttpRequest, obj: any, form: ModelForm, change: bool
    ) -> None:
        with transaction.atomic():
            if change:
                PaymentService.rollback(obj)
                before_obj= Payment.objects.get(pk=obj.pk)
                before= serializer_inst(before_obj)

                super().save_model(request, obj, form, change)

                PaymentService.allocate(obj)
                after=serializer_inst(obj)
                reason=form.cleaned_data.get('reason')

                AuditLog.objects.create(
                    user=obj.customer.owner,
                    before=before,
                    after=after,
                    action='u',
                    model='p',
                    reason=reason,
                )

            else:
                super().save_model(request, obj, form, change)
                PaymentService.allocate(obj)


@admin.register(Allocation)
class AllocationAdmin(ReadOnlyModelAdmin):
    list_display= [
        'record',
        'payment',
        'amount',
        'created_at',
    ]
    search_fields=[
        'record__customer__logo',
        'record__customer__name',
        'record',
        'payment'
    ]
    list_filter=[
        'created_at',
    ]


@admin.register(Advance)
class AdvanceAdmin(ReadOnlyModelAdmin):
    list_display=[
        'customer',
        'total_amount',
        'payment',
        'created_at',
    ]
    search_fields = [
        "customer__logo",
        "customer__name",
    ]
    list_filter=[
        'created_at'
    ]


@admin.register(AdvanceUsage)
class AdvanceUsageAdmin(ReadOnlyModelAdmin):
    list_display=[
        'advance',
        'record',
        'amount',
        'created_at',
    ]
    search_fields=[
        'advance__customer__logo',
        'advance__customer__name',
    ]
    list_filter=[
        'created_at'
    ]


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnlyModelAdmin):
    list_display=[
        'user',
        'logged_at',
        'before',
        'after',
        'model',
        'action',
        'reason',
    ]
    search_fields=[
        'user__username',
    ]
    list_filter=[
        'logged_at',
        'model',
        'action',
    ]



# class Request(models.Model):
#     owner = models.ForeignKey(user, on_delete=models.CASCADE,
#                               related_name='requester')
#     record=models.ManyToManyField(Record)
#     amount=models.DecimalField(max_digits=10, decimal_places=2)
#     created_at=models.DateField(default=timezone.localdate)
#     reason=models.TextField(blank=True, null=True)
#     status= models.CharField(max_length=1,
#                              choices=[('p', 'PENDING'), ('a', 'APPROVED'), ('r', 'REJECTED')],
#                              default='p')

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):

    # view methods
    def get_record(self, obj):
        return ', '.join(str(r) for r in Record.objects.all())

    list_display=[
        'owner',
        'get_record',
        'amount',
        'created_at',
        'status',
        'reason',
    ]
    search_fields=[
        'owner__username',
    ]
    list_filter=[
        'created_at',
        'status',
        'owner__username'
    ]
