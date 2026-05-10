from .models import Record, Allocation, Payment
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal


class PaymentService:

    @staticmethod
    def allocate(payment):
        records = (
            Record.objects.filter(customer=payment.customer)
            .order_by("created_at")
            .annotate(  # ← annotate here too
                _paid_amount=Coalesce(
                    Sum("allocation__amount"), Value(0), output_field=DecimalField()
                )
            )
        )

        remains = payment.amount

        for record in records:
            if remains <= 0:
                break

            due = record.amount - ((record.discount or 0) + (record._paid_amount or 0))

            if due <= 0:
                continue

            allocated = min(due, remains)

            Allocation.objects.create(
                record=record,
                amount=allocated,
                payment=payment,
            )

            remains -= allocated

    @staticmethod
    def rollback(payment):
        Allocation.objects.filter(payment=payment).delete()
