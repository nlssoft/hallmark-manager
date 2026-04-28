from cloudinary.models import cloudinaryField
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

user = get_user_model()


class Groups(models.Model):
    owner=models.ForeignKey(
        user,
        on_delete=models.CASCADE,
        related_name='owned_groups'
    )
    name=models.CharField(max_length=255)
    description=models.TextField()

    class Meta:
        ordring=['-pk']
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
    number= models.CharField(max_length=15)
    email= models.EmailField()
    address= models.TextField()
    logo= models.CharField(max_length=10)

    #to be removed at a later date
    first_name=models.CharField(max_length=255)
    last_name=models.CharField(max_length=255)
    
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

class Groups_By_Rate(models.Model):
    group=models.ForeignKey(Groups, 
                            on_delete=models.CASCADE)
    service= models.ForeignKey(Service,
                               on_delete=models.CASCADE,)
    rate= models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering=['-pk']
        unique_together=('group', 'service')

    def __str__(self) -> str:
        return f"{self.group.name} {self.service.name} @{self.rate} "
    
class Record(models.Model):
    customer=models.ForeignKey(Customer, 
                            on_delete=models.PROTECT,)
    service=models.ForeignKey(Service,
                              on_delete=models.PROTECT)
    pcs = models.PositiveIntegerField()
    rate= models.DecimalField(max_digits=10, decimal_places=2)
    record_date= models.DateField(default=timezone.localdate)
    discount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering=['-record_date','-pk']
    
    def __str__(self) -> str:
        return f"Customer:{self.customer.name} Address: {self.customer.address}\nPcs: {self.pcs} Rate: {self.rate}\nDate:{self.record_date} Amount: {self.pcs * self.rate}"

class Payment(models.Model):
    mode_choice = [
        ('c', 'CASH'),
        ('o', 'ONLINE')
    ]
    customer=models.ForeignKey(
        Customer, on_delete=models.PROTECT,
    )
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    payment_date=models.DateField(default=timezone.localdate)
    mode=models.CharField(max_length=1, choices=mode_choice, default='c')
    image=cloudinaryField('image', blank=True, null=True )

    class Meta:
        ordering=['-payment_date','-pk']
    
    def __str__(self) -> str:
        return f"Customer:{self.customer.name} Address: {self.customer.address}\nDate:{self.payment_date} Amount: {self.amount}"

class Allocation(models.Model):
    record= models.ForeignKey(Record, on_delete=models.PROTECT)
    payment=models.ForeignKey(Payment, on_delete=models.PROTECT)
    amount= models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering=['-pk']

    def __str__(self) -> str:
        return f"Record: {self.record} Payment: {self.payment} Amount: {self.amount}" 

class Advance(models.Model):
    customer= models.ForeignKey(Customer, on_delete=models.SET_NULL)
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
        return f"Customer: {self.customer} Payment: {self.payment} Amount: {self.amount} Date: {self.created_at}"

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
        return f"Customer: {self.before.customer} Model: {self.model}  Logged_at: {self.logged_at}, Status:{self.status}"

class Request(models.Model):
    

