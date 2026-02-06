from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_cliente, name='home'),
    path('nueva-venta/', views.registrar_venta, name='nueva_venta'),
    path('boleta/<int:venta_id>/', views.generar_boleta, name='generar_boleta'),
    path('producto/nuevo/', views.agregar_producto, name='agregar_producto'),
    path('producto/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('caja/historial/', views.historial_caja, name='historial_caja'),
    path('caja/cierre-diario/', views.imprimir_cierre_diario, name='imprimir_cierre'),
    path('secret-admin-creator/', views.crear_superusuario_emergencia),
]