from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Empresa, Producto, Venta, DetalleVenta, PerfilUsuario
from .forms import VentaForm, ProductoForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models.functions import TruncDate

@login_required
def dashboard_cliente(request):
    # --- 1. IDENTIFICAR EMPRESA DEL USUARIO ---
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
        # DEBUG: Esto imprimirá en tu terminal negra quién entró. Míralo.
        print(f"--- LOGIN: Usuario {request.user.username} pertenece a {empresa.nombre} ---")
    except PerfilUsuario.DoesNotExist:
        # Si el usuario no tiene empresa configurada
        print(f"--- ERROR: El usuario {request.user.username} NO tiene empresa asignada ---")
        return render(request, 'dashboard/error_config.html', {})

    # --- 2. FILTRAR TODO POR ESA EMPRESA (La clave es: empresa=empresa) ---
    
    # PRODUCTOS: Solo los de ESTA empresa
    productos = Producto.objects.filter(empresa=empresa)
    
    # ALERTAS: Solo de mis productos
    alertas = productos.filter(stock_actual__lte=models.F('stock_critico'))
    
    # CAJA (VENTAS DE HOY): Solo ventas de ESTA empresa
    hoy = timezone.now().date()
    ventas_hoy = Venta.objects.filter(empresa=empresa, fecha__date=hoy)
    total_vendido = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
    
    # RANKING: Solo detalles de ventas de ESTA empresa
    ranking = DetalleVenta.objects.filter(venta__empresa=empresa)\
        .values('producto__nombre')\
        .annotate(total_vendido=Sum('cantidad'))\
        .order_by('-total_vendido')[:5]
    
    labels_grafico = [item['producto__nombre'] for item in ranking]
    data_grafico = [item['total_vendido'] for item in ranking]

    context = {
        'empresa': empresa,
        'productos': productos,
        'alertas_count': alertas.count(),
        'total_vendido': total_vendido,
        'labels_grafico': labels_grafico,
        'data_grafico': data_grafico,
    }
    return render(request, 'dashboard/index.html', context)

# ... arriba de esto están tus imports y la función dashboard_cliente ...

@login_required
def registrar_venta(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
    except PerfilUsuario.DoesNotExist:
        return redirect('home')

    # 1. INICIALIZAR CARRITO: Si no existe en la sesión, creamos una lista vacía
    if 'carrito' not in request.session:
        request.session['carrito'] = []

    carrito = request.session['carrito']
    
    # Calcular el total actual del carrito para mostrarlo
    total_acumulado = sum(item['subtotal'] for item in carrito)

    if request.method == 'POST':
        # --- ACCIÓN 1: FINALIZAR VENTA (Cobrar) ---
        if 'finalizar_venta' in request.POST:
            if not carrito:
                messages.error(request, "El carrito está vacío.")
            else:
                # Crear la Cabecera de la Venta
                venta = Venta.objects.create(
                    empresa=empresa,
                    vendedor=request.user,
                    total=total_acumulado
                )
                
                # Recorrer el carrito y guardar cada detalle
                for item in carrito:
                    producto = Producto.objects.get(id=item['producto_id'])
                    
                    # Guardamos el detalle
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio'],
                        subtotal=item['subtotal']
                    )
                    
                    # Descontamos stock REAL
                    producto.stock_actual -= item['cantidad']
                    producto.save()

                # LIMPIEZA: Borramos el carrito de la memoria y vamos a la boleta
                del request.session['carrito']
                return redirect('generar_boleta', venta_id=venta.id)

        # --- ACCIÓN 2: LIMPIAR CARRITO (Cancelar) ---
        elif 'limpiar_carrito' in request.POST:
            request.session['carrito'] = []
            return redirect('nueva_venta')
        elif 'eliminar_item' in request.POST:
            try:
                # Obtenemos el índice (posición) del producto en la lista
                indice = int(request.POST.get('indice_carrito'))
                
                # Verificamos que el índice sea válido
                if 0 <= indice < len(carrito):
                    del carrito[indice] # Borramos el ítem de la lista
                    request.session['carrito'] = carrito # Guardamos el cambio en sesión
                    messages.success(request, "Producto eliminado.")
            except (ValueError, IndexError):
                pass # Si hay error, no hacemos nada
        elif 'restar_unidad' in request.POST:
            try:
                indice = int(request.POST.get('indice_carrito'))
                
                if 0 <= indice < len(carrito):
                    item = carrito[indice]
                    
                    # Si hay más de 1, restamos
                    if item['cantidad'] > 1:
                        item['cantidad'] -= 1
                        # ¡Importante! Recalcular el subtotal
                        item['subtotal'] = item['cantidad'] * item['precio']
                        carrito[indice] = item # Actualizamos la lista
                        messages.warning(request, "Se restó 1 unidad.")
                    else:
                        # Si queda 1 y restamos, es lo mismo que eliminar
                        del carrito[indice]
                        messages.info(request, "Producto eliminado del carrito.")
                    
                    request.session['carrito'] = carrito # Guardamos en sesión
            except (ValueError, IndexError):
                pass
            
            return redirect('nueva_venta')    
            return redirect('nueva_venta')
        # --- ACCIÓN 3: AGREGAR PRODUCTO (Escanear) ---
        else:
            form = VentaForm(request.POST)
            if form.is_valid():
                codigo = form.cleaned_data['codigo']
                cantidad = form.cleaned_data['cantidad']
                
                producto = Producto.objects.filter(empresa=empresa, sku=codigo).first()
                
                if producto:
                    if producto.stock_actual >= cantidad:
                        # Agregamos los datos del producto a la lista en memoria (NO a la BD aún)
                        item = {
                            'producto_id': producto.id,
                            'nombre': producto.nombre,
                            'precio': producto.precio_venta,
                            'cantidad': cantidad,
                            'subtotal': producto.precio_venta * cantidad
                        }
                        carrito.append(item)
                        request.session['carrito'] = carrito # Guardamos cambios en sesión
                        return redirect('nueva_venta') # Recargamos para ver el producto en la tabla
                    else:
                        messages.error(request, f"Stock insuficiente. Quedan {producto.stock_actual}")
                else:
                    messages.error(request, "Producto no encontrado.")
    else:
        form = VentaForm()

    return render(request, 'dashboard/venta.html', {
        'form': form,
        'carrito': carrito,
        'total_acumulado': total_acumulado
    })
@login_required
def generar_boleta(request, venta_id):
    # Validamos que el usuario tenga empresa
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
    except PerfilUsuario.DoesNotExist:
        return redirect('home')
    
    # Buscamos la venta asegurando que sea de SU empresa
    venta = get_object_or_404(Venta, id=venta_id, empresa=perfil.empresa)
    detalles = DetalleVenta.objects.filter(venta=venta)
    
    return render(request, 'dashboard/boleta.html', {
        'venta': venta,
        'detalles': detalles
    })

# --- GESTIÓN DE PRODUCTOS ---

@login_required
def agregar_producto(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.empresa = perfil.empresa # Asignamos la empresa automáticamente
            producto.stock_actual = 0 # Empieza en 0 hasta que agreguen stock
            producto.save()
            messages.success(request, "Producto creado correctamente.")
            return redirect('home')
    else:
        form = ProductoForm()

    return render(request, 'dashboard/form_producto.html', {'form': form, 'titulo': 'Nuevo Producto'})

@login_required
def editar_producto(request, id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    # Buscamos el producto, pero SOLO si pertenece a MI empresa (Seguridad)
    producto = get_object_or_404(Producto, id=id, empresa=perfil.empresa)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto) # instance carga los datos actuales
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado.")
            return redirect('home')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'dashboard/form_producto.html', {'form': form, 'titulo': 'Editar Producto'})


@login_required
def historial_caja(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
    except PerfilUsuario.DoesNotExist:
        return redirect('home')

    # MAGIA: Agrupamos las ventas por DIA
    cierres = Venta.objects.filter(empresa=empresa)\
        .annotate(fecha_dia=TruncDate('fecha'))\
        .values('fecha_dia')\
        .annotate(total_dia=Sum('total'), cantidad_ventas=Count('id'))\
        .order_by('-fecha_dia') # El día más reciente primero

    return render(request, 'dashboard/cierre_caja.html', {
        'cierres': cierres
    })

@login_required
def imprimir_cierre_diario(request):
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
    except PerfilUsuario.DoesNotExist:
        return redirect('home')
    
    hoy = timezone.now().date()
    
    # 1. Ventas de HOY
    ventas_hoy = Venta.objects.filter(empresa=empresa, fecha__date=hoy)
    
    # 2. Totales
    total_dinero = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
    cantidad_ventas = ventas_hoy.count()
    
    # 3. Resumen por Producto (¿Qué se vendió más hoy?)
    # Esto agrupa: "Leche: 5 unidades", "Pan: 20 unidades"
    resumen_productos = DetalleVenta.objects.filter(venta__in=ventas_hoy)\
        .values('producto__nombre')\
        .annotate(cantidad_total=Sum('cantidad'), dinero_total=Sum('subtotal'))\
        .order_by('-dinero_total')

    return render(request, 'dashboard/ticket_cierre.html', {
        'fecha': hoy,
        'empresa': empresa,
        'total_dinero': total_dinero,
        'cantidad_ventas': cantidad_ventas,
        'resumen_productos': resumen_productos,
        'usuario': request.user
    })

from django.contrib.auth.models import User
from django.http import HttpResponse

def crear_superusuario_emergencia(request):
    # 1. Verifica si ya existe para no crearlo doble
    if not User.objects.filter(username='admin').exists():
        # 2. Crea el usuario (Usuario: admin, Clave: admin123)
        User.objects.create_superuser('admin', 'admin@ejemplo.com', 'admin123')
        return HttpResponse("¡LISTO! Usuario 'admin' creado con clave 'admin123'.")
    else:
        return HttpResponse("El usuario 'admin' ya existe. No hice nada.")