from django.contrib import admin
from django.forms.models import ModelForm
from django.http import HttpRequest
from .models import (
    Groups,
    Customer,
    Service,
    Rate_Group,
    Record,
    Payment,
    Advance,
    AdvanceUsage,
    AuditLog,
    Request,
)
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


@admin.register(Rate_Group)
class Rate_GroupAdmin(admin.ModelAdmin):
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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _paid_amount=Coalesce(
                    Sum("allocation__amount"), Value(0), output_field=DecimalField()
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
    def delete_model(self, request: HttpRequest, obj: any) -> None:
        with transaction.atomic():
            affected_payments = list(
                Payment.objects.filter(allocation__record=obj).distinct()
            )
            obj.delete()

            for payment in affected_payments:
                PaymentService.rollback(payment)
                PaymentService.allocate(payment)

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
                super().save_model(request, obj, form, change)
                PaymentService.allocate(obj)
            else:
                super().save_model(request, obj, form, change)
                PaymentService.allocate(obj)


# class Allocation(models.Model):
#     record= models.ForeignKey(Record, on_delete=models.PROTECT)
#     payment=models.ForeignKey(Payment, on_delete=models.PROTECT)
#     amount= models.DecimalField(max_digits=10, decimal_places=2)

#     class Meta:
#         ordering=['-pk']

#     def __str__(self) -> str:
#         return f"Record: {self.record} Payment: {self.payment} Amount: {self.amount}"

# class Advance(models.Model):
#     customer= models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
#     total_amount= models.DecimalField(max_digits=10, decimal_places=2)
#     payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
#     created_at= models.DateTimeField(default=timezone.now)

#     class Meta:
#         ordering=['-pk']

#     def __str__(self) -> str:
#         return f"Customer: {self.customer} Payment: {self.payment} Amount: {self.amount} Date: {self.created_at}"

# class AdvanceUsage(models.Model):
#     advance = models.ForeignKey(Advance, on_delete=models.CASCADE)
#     record = models.ForeignKey(Record, on_delete=models.CASCADE)
#     amount= models.DecimalField(max_digits=10, decimal_places=2)
#     created_at = models.DateTimeField(default=timezone.now)


#     class Meta:
#         ordering=['-pk']

#     def __str__(self) -> str:
#         return f"Record: {self.record} \
#             Amount: {self.amount} Date: {self.created_at}"

# class AuditLog(models.Model):
#     model_choice= [
#         ('r', 'Record'),
#         ('p', 'Payment')
#     ]
#     status_choice=[
#         ('a', 'Approved'),
#         ('p', 'Pending'),
#         ('r', 'Rejected'),
#     ]
#     user = models.ForeignKey(user, on_delete=models.CASCADE)
#     before= models.JSONField(null=True, blank=True)
#     after= models.JSONField(null=True, blank=True)
#     logged_at= models.DateTimeField(default=timezone.now)
#     model= models.CharField(max_length=1, choices=model_choice)
#     status= models.CharField(max_length=1, choices=status_choice, default='p')

#     class Meta:
#         ordering=['-pk']

#     def __str__(self) -> str:
#         return f"Customer: {self.before.customer} Model: {self.model}  \
#             Logged_at: {self.logged_at}, Status:{self.status}"

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


#     class Meta:
#         ordering=['-pk']
