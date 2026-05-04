from cloudinary.models import CloudinaryField
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum


user = get_user_model()


class Groups(models.Model):
    owner=models.ForeignKey(
        user,
        on_delete=models.CASCADE,
        related_name='owned_groups'
    )
    name=models.CharField(max_length=255)
    description=models.TextField(null=True, blank=True)

    class Meta:
        ordering=['-pk']
        unique_together=('owner', 'name')
    
    def __str__(self) -> str:
        return f"Name: {self.name} Description: {self.description}"

class Customer(models.Model):
    owner= models.ForeignKey(user, 
                             on_delete=models.CASCADE, 
                             related_name='owned_parties')
    
    assigned_to=models.ForeignKey(user, 
                                  on_delete=models.SET_NULL, 
                                  null=True, blank=True,
                                  related_name='assigned_parties')
    
    group= models.ForeignKey(Groups, 
                             on_delete=models.SET_NULL, 
                             null=True, blank=True)

    name=models.CharField(max_length=455)
    number= models.CharField(max_length=15, null=True, blank=True)
    email= models.EmailField(null=True, blank=True, unique=True)
    address= models.TextField(null=True, blank=True)
    logo= models.CharField(max_length=10, null=True, blank=True)
    
    def __str__(self) -> str:
        return f"{self.name} {self.address}"
    
    class Meta:
        ordering=['-pk']
    
class Service(models.Model):
    owner= models.ForeignKey(user, 
                             on_delete=models.CASCADE,
                             related_name='owned_service')
    name=models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.name}"
    
    class Meta:
        ordering=['name']
        unique_together=('owner', 'name')

class Rate_Group(models.Model):
    group=models.ForeignKey(Groups, 
                            on_delete=models.CASCADE)
    service= models.ForeignKey(Service,
                               on_delete=models.CASCADE,)
    rate= models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering=['-pk']
        unique_together=('group', 'service')

    def __str__(self) -> str:
        return f"{self.group} {self.service} @{self.rate} "
    
class Record(models.Model):
    customer=models.ForeignKey(Customer, 
                            on_delete=models.PROTECT,)
    service=models.ForeignKey(Service,
                              on_delete=models.PROTECT)
    pcs = models.PositiveIntegerField()
    rate= models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at= models.DateField(default=timezone.localdate)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True )

    class Meta:
        ordering=['-created_at','-pk']
    
    def __str__(self) -> str:
        return f"Customer:{self.customer}\nPcs: {self.pcs} \
            Rate: {self.rate}\nDate:{self.created_at} Amount: {self.pcs * self.rate}"
    
    # derived values
    @property
    def amount(self):
        return (self.rate or 0) * (self.pcs or 0)


    # methods
    def save(self, *args, **kwargs):
        if not self.rate:
            try:
                rate_obj= Rate_Group.objects.get(
                    group=self.customer.group,
                    service= self.service
                )
                self.rate=rate_obj.rate
            except Rate_Group.DoesNotExist:
                raise ValidationError(
                    'No rate defined for this customer and service.'
                )

            super().save(*args, **kwargs)


class Payment(models.Model):
    mode_choice = [
        ('c', 'CASH'),
        ('o', 'ONLINE')
    ]
    customer=models.ForeignKey(
        Customer, on_delete=models.PROTECT,
    )
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    created_at=models.DateField(default=timezone.localdate)
    mode=models.CharField(max_length=1, choices=mode_choice, default='c')
    image=CloudinaryField('image', blank=True, null=True )

    class Meta:
        ordering=['-created_at','-pk']
    
    def __str__(self) -> str:
        return f"Customer:{self.customer} Date:{self.created_at} Amount: {self.amount}"

class Allocation(models.Model):
    record= models.ForeignKey(Record, on_delete=models.PROTECT)
    payment=models.ForeignKey(Payment, on_delete=models.PROTECT)
    amount= models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering=['-pk']

    def __str__(self) -> str:
        return f"Record: {self.record} Payment: {self.payment} Amount: {self.amount}" 

class Advance(models.Model):
    customer= models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    total_amount= models.DecimalField(max_digits=10, decimal_places=2)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    created_at= models.DateTimeField(default=timezone.now)

    class Meta:
        ordering=['-pk']

    def __str__(self) -> str:
        return f"Customer: {self.customer} Payment: {self.payment} Amount: {self.amount} Date: {self.created_at}"

class AdvanceUsage(models.Model):
    advance = models.ForeignKey(Advance, on_delete=models.CASCADE)
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    amount= models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    

    class Meta:
        ordering=['-pk']

    def __str__(self) -> str:
        return f"Record: {self.record} \
            Amount: {self.amount} Date: {self.created_at}"

class AuditLog(models.Model):
    model_choice= [
        ('r', 'Record'),
        ('p', 'Payment')
    ]
    status_choice=[
        ('a', 'Approved'),
        ('p', 'Pending'),
        ('r', 'Rejected'),
    ]
    user = models.ForeignKey(user, on_delete=models.CASCADE)
    before= models.JSONField(null=True, blank=True)
    after= models.JSONField(null=True, blank=True)
    logged_at= models.DateTimeField(default=timezone.now)
    model= models.CharField(max_length=1, choices=model_choice)
    status= models.CharField(max_length=1, choices=status_choice, default='p') 

    class Meta:
        ordering=['-pk']

    def __str__(self) -> str:
        return f"Customer: {self.before.customer} Model: {self.model}  \
            Logged_at: {self.logged_at}, Status:{self.status}"

class Request(models.Model):
    owner = models.ForeignKey(user, on_delete=models.CASCADE,
                              related_name='requester')
    record=models.ManyToManyField(Record)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    created_at=models.DateField(default=timezone.localdate)
    reason=models.TextField(blank=True, null=True)
    status= models.CharField(max_length=1, 
                             choices=[('p', 'PENDING'), ('a', 'APPROVED'), ('r', 'REJECTED')], 
                             default='p')

    
    class Meta:
        ordering=['-pk']

