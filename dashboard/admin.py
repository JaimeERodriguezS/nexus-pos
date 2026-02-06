from django.contrib import admin
from .models import Empresa, PerfilUsuario, Producto

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'rubro', 'fecha_creacion')
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sku', 'stock_actual', 'precio_venta', 'empresa')
    list_filter = ('empresa',) # Filtro lateral útil para cuando tengas varios clientes


# Registramos los otros modelos de forma simple
admin.site.register(PerfilUsuario)