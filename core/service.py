from .models import Record, Allocation, Payment, Advance, AdvanceUsage
from django.db.models import Sum, F, Value, DecimalField
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
        due = record.amount - ((record.discount or 0))
     
        if due <= 0:
            return
        
        # all advance row that exists
        advance_query_set = Advance.objects.filter(customer=customer).order_by('created_at')

        for advance in advance_query_set:
            # if ever due goes beneth 0 break the loop
            if due <= 0:
                break
            
            # for this advance what amount is still unallocated
            used_already = AdvanceUsage.objects.filter(advance=advance)\
                .aggregate(total = Sum('amount'))['total'] or 0
            
            available= advance.total_amount - used_already

            # if there is none then skip this advance row and move to next row
            if available <= 0:
                continue

            used = min(available, due )

            AdvanceUsage.objects.create(
                advance=advance,
                amount= used,
                record= record,
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

        #advance allocation
        if remains > 0:
            PaymentService.advance_create(payment, remains)

    @staticmethod
    def rollback(payment):
        Allocation.objects.filter(payment=payment).delete()
        Advance.objects.filter(payment=payment).delete()

    @staticmethod
    def rollback_plus_allocate(payment):
        PaymentService.rollback(payment)
        PaymentService.allocate(payment)