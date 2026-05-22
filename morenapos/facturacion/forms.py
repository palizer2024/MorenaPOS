from django import forms
from .models import ComprobanteClonado, SedeClonada


class InvoceForm(forms.Form):
    cliente_id = forms.IntegerField()
    sede_id = forms.IntegerField()
    serie = forms.CharField(max_length=10)
    productos = forms.JSONField(required=False)