from .models import Record, Allocation, Payment, Advance, AdvanceUsage
from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from decimal import Decimal


class PaymentService:

    @staticmethod
    def advance_create(payment, amount):
        Advance.objects.create(
            customer=payment.customer,
            total_amount=amount,
            payment=payment,
        )

    @staticmethod
    def advance_allocate(record):
        customer = record.customer
        try:
            due = record._left
        except AttributeError:
            due = record.amount - ((record.discount or 0))

        if due <= 0:
            return

        # all advance row that exists
        advance_query_set = (
            Advance.objects.filter(customer=customer)
            .annotate(
                _used_already=Coalesce(
                    Sum("advanceusage__amount"), Value(0), output_field=DecimalField()
                )
            )
            .annotate(_available=F("total_amount") - F("_used_already"))
            .filter(_available__gt=0)
            .order_by("created_at")
        )

        for advance in advance_query_set:
            # if ever due goes beneth 0 break the loop
            if due <= 0:
                break

            available = advance._available

            # if there is none then skip this advance row and move to next row
            if available <= 0:
                continue

            used = min(available, due)

            AdvanceUsage.objects.create(
                advance=advance,
                amount=used,
                record=record,
            )

            # minus the avilable amount from due so at some point nothing exists
            due -= used

    @staticmethod
    def allocate(payment):
        records = (
            Record.objects.filter(customer=payment.customer)
            .order_by("created_at")
            .annotate(  # ← annotate here too
                _paid_amount=Coalesce(
                    Sum("allocation__amount"), Value(0), output_field=DecimalField()
                )
                + Coalesce(
                    Sum("advanceusage__amount"), Value(0), output_field=DecimalField()
                )
            )
            .annotate(
                _amount=Coalesce(
                    F("rate") * F("pcs"), Value(0), output_field=DecimalField()
                )
            )
            .annotate(
                _due=F("_amount")
                - F("_paid_amount")
                - Coalesce(F("discount"), Value(0), output_field=DecimalField())
            )
        )

        remains = payment.amount

        for record in records:
            if remains <= 0:
                break

            due = record._due

            if due <= 0:
                continue

            allocated = min(due, remains)

            Allocation.objects.create(
                record=record,
                amount=allocated,
                payment=payment,
            )

            remains -= allocated

        # advance allocation
        if remains > 0:
            PaymentService.advance_create(payment, remains)

    @staticmethod
    def allocate_selected(records):

        for record in records:
            payment = Payment.objects.create(
                customer=record.customer, amount=record._due, mode="c"
            )
            Allocation.objects.create(
                payment=payment, record=record, amount=payment.amount
            )

    @staticmethod
    def record_rollback(record):
        Allocation.objects.filter(record=record).delete()
        AdvanceUsage.objects.filter(record=record).delete()

    @staticmethod
    def Payment_rollback(payment):
        Allocation.objects.filter(payment=payment).delete()
        Advance.objects.filter(payment=payment).delete()

    @staticmethod
    def rollback_plus_allocate(payment):
        PaymentService.rollback(payment)
        PaymentService.allocate(payment)

    @staticmethod
    def re_balance(customer):
        # All payments for this customer, oldest first
        payments = (
            Payment.objects.filter(customer=customer)
            .annotate(
                used=Coalesce(
                    Sum("allocation__amount"), Value(0), output_field=DecimalField()
                )
                + Coalesce(
                    Sum("advance__total_amount"), Value(0), output_field=DecimalField()
                )
            )
            .annotate(_left=F("amount") - F("used"))
            .filter(_left__gt=0)
            .order_by("created_at")
        )

        # All unpaid records, oldest first
        records = (
            Record.objects.filter(customer=customer)
            .annotate(
                _paid=Coalesce(
                    Sum("allocation__amount"), Value(0), output_field=DecimalField()
                )
                + Coalesce(
                    Sum("advanceusage__amount"), Value(0), output_field=DecimalField()
                ),
                _due=F("rate") * F("pcs")
                - F("_paid")
                - Coalesce(F("discount"), Value(0), output_field=DecimalField()),
            )
            .filter(_due__gt=0)
            .order_by("created_at")
        )

        for payment in payments:
            unallocated = payment._left

            if unallocated <= 0:
                continue

            for record in records:
                if record._due <= 0:
                    continue

                apply = min(unallocated, record._due)
                Allocation.objects.create(payment=payment, record=record, amount=apply)
                record._due -= apply
                unallocated -= apply

                # break the inner Loop if payment._left is finshied
                if unallocated <= 0:
                    break

            if unallocated > 0:
                PaymentService.advance_create(payment, unallocated)

                unallocated = 0

        # Now after this if there is some unpaid record left
        # then run advance on them

        records = records.filter(_due__gt=0)

        if records:
            for record in records:
                PaymentService.advance_allocate(record)
