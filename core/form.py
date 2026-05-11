from django import forms
from .models import Record, Payment


class ReasonForm(forms.ModelForm):
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows':3}),
        help_text='Explain why this change was made.'    
    )

class RecordAdminForm(ReasonForm):
    class Meta:
        model = Record
        fields = '__all__'


class PaymentAdminForm(ReasonForm):
    class Meta:
        model = Payment
        fields = '__all__'