from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
import json

def serializer_inst(obj):
    data={}
    
    for field in obj._meta.fields:
        value= getattr(obj, field.attname)
        try:
            json.dumps(value)
            data[field.name]=value            
        except (TypeError, ValueError):
            data[field.name]= str(value)
    return data
        
    