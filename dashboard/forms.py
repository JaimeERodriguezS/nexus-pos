from django import forms
from .models import Producto

from django.forms import ModelForm # <--- Agrega esto si no está

class ProductoForm(ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'sku', 'precio_venta', 'stock_critico'] # No ponemos stock_actual ni empresa
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_critico': forms.NumberInput(attrs={'class': 'form-control'}),
        }
class VentaForm(forms.Form):
    # Antes era ModelChoiceField (Lista), ahora es CharField (Texto)
    codigo = forms.CharField(
        label="Escanea el código del producto", 
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', # Clase CSS para que se vea grande
            'autofocus': 'autofocus', # <--- MAGIA: El cursor aparece aquí solo
            'placeholder': 'Dispara aquí...'
        })
    )
    cantidad = forms.IntegerField(
        min_value=1, 
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
