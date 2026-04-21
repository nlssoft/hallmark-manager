from django.db import models
from django.contrib.auth import get_user_model

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

class Party(models.Model):
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

    
    first_name=models.CharField(max_length=255)
    last_name=models.CharField(max_length=255)
    number= models.CharField(max_length=15)
    email= models.EmailField()
    address= models.TextField()
    logo= models.CharField(max_length=10)
    
    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        ordering=['-pk']
    
class Service_Type(models.Model):
    owner= models.ForeignKey(user, 
                             on_delete=models.CASCADE,
                             related_name='owned_service')
    type_of_service=models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.type_of_service}"
    
    class Meta:
        ordering=['type_of_service']
        unique_together=('owner', 'type_of_service')

class Groups_By_Rate(models.Model):
    group=models.ForeignKey(Groups, 
                            on_delete=models.CASCADE)
    service= models.ForeignKey(Service_Type,
                               on_delete=models.CASCADE,)
    rate= models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering=['-pk']
        unique_together=('group', 'service')

    def __str__(self) -> str:
        return f"{self.group.name} {self.service.type_of_service} @{self.rate} "
    
class Record(models.Model):
    party=models.ForeignKey(Party, 
                            on_delete=models.PROTECT,)
    service=models.ForeignKey(Service_Type,
                              on_delete=models.PROTECT)
    pcs = models.PositiveIntegerField()
    rate= models.DecimalField(max_digits=10, decimal_places=2)
    record_date= models.DateField()
    discount = models.DecimalField(max_digits=10, decimal_places=2)