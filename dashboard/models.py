from django.db import models
from django.contrib.auth.models import User

# 1. Modelo Empresa: Para que el sistema sepa de quién son los datos
class Empresa(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, help_text="Formato: 12.345.678-9")
    rubro = models.CharField(max_length=50, blank=True) # Ej: Panadería, Taller, Planta
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

# 2. Perfil de Usuario extendido: Vincula un usuario (login) con una Empresa
class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cargo = models.CharField(max_length=50) # Ej: Dueño, Operario, Contador

    def __str__(self):
        return f"{self.user.username} - {self.empresa.nombre}"

# 3. Inventario/Productos: Lo básico que cualquier Pyme necesita controlar
class Producto(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE) # Clave para separar clientes
    nombre = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, blank=True)
    stock_actual = models.IntegerField(default=0)
    stock_critico = models.IntegerField(default=5, help_text="Avisar si baja de este número")
    precio_venta = models.IntegerField()
    
    def __str__(self):
        return f"{self.nombre} ({self.stock_actual})"


class Venta(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # Para saber quién vendió
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Venta #{self.id} - ${self.total}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.IntegerField() # Guardamos el precio del momento (por si cambia después)
    subtotal = models.IntegerField()

    def save(self, *args, **kwargs):
        # Calculamos el subtotal automático
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)