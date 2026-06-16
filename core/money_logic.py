from .models import Record, Allocation, Payment, Advance, AdvanceUsage, Customer
from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from decimal import Decimal


class PaymentService:

    @staticmethod
    def use_remain(payment, records, remains):
        
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
        return remains

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
            Advance.objects.with_availability().filter(customer=customer, _available__gt=0)
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
    def allocate(payment, remains=None):
        records = Record.objects.with_financials().filter(
            customer=payment.customer).order_by("created_at")
        
        if remains is None:
            remains = payment.amount

        remains = PaymentService.use_remain(payment, records, remains)

        # advance allocation
        if remains > 0:
            PaymentService.advance_create(payment, remains)

    @staticmethod
    def allocate_selected(record):
        payment = Payment.objects.create(
            customer=record.customer, amount=record._due, mode="c"
        )
        Allocation.objects.create(
            payment=payment, record=record, amount=payment.amount
        )
    
    @staticmethod
    def allocate_selected_many(records):
        
        customers = Customer.objects.filter(record__in=records).distinct()

        for customer in customers:
            customer_records = records.filter(customer=customer)

            total_due = sum(r._due for r in customer_records)

            payment = Payment.objects.create(
                customer=customer, amount=total_due, mode='c'
            )

            allocation = [
                Allocation(
                    payment=payment,
                    record=r,
                    amount=r._due
                )
                for r in customer_records
            ] 

            Allocation.objects.bulk_create(allocation)

    @staticmethod
    def record_rollback(record):
        Allocation.objects.filter(record=record).delete()
        AdvanceUsage.objects.filter(record=record).delete()

    @staticmethod
    def Payment_rollback(payment):
        allocation_record = list(Allocation.objects.filter(payment=payment).values_list('record_id', flat=True))
        advanceusage_record = list(AdvanceUsage.objects.filter(advance__payment=payment).values_list('record_id', flat=True))

        Allocation.objects.filter(payment=payment).delete()
        Advance.objects.filter(payment=payment).delete()

        return allocation_record, advanceusage_record

    @staticmethod
    def update_allocate(payment, allocation_record, advanceusage_record):
        
        remains = payment.amount

        if allocation_record:
            records = Record.objects.with_financials().filter(pk__in=allocation_record).order_by('created_at', 'pk')

            remains = PaymentService.use_remain(payment, records, remains)


        if remains > Decimal('0.00') and advanceusage_record:
            records = list(Record.objects.with_financials().filter(pk__in=advanceusage_record).order_by('created_at', 'pk'))
            records_due = sum(r._due for r in records)

            safe = min(remains, records_due)

            advance = Advance.objects.create(
                payment=payment, 
                customer=payment.customer,
                total_amount= safe)
            
            advance_remaining = safe
            
            for record in records:
                if advance_remaining <= Decimal('0.00'):
                    break

                used= min(record._due, advance_remaining)

                AdvanceUsage.objects.create(
                    record = record,
                    advance=advance,
                    amount=used
                )

                advance_remaining -= used
                remains -= used
    
        if remains > Decimal('0.00'):
            PaymentService.allocate(payment, remains)


    @staticmethod
    def rollback_plus_allocate(payment):
        PaymentService.rollback(payment)
        PaymentService.allocate(payment)

    @staticmethod
    def re_balance(customer):
        # All payments for this customer, oldest first
        payments = (
            Payment.objects.with_balance().filter(customer=customer)
            .filter(_left__gt=0)
            .order_by("created_at")
        )

        # All unpaid records, oldest first
        records = (
            Record.objects.with_financials().filter(customer=customer)
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
