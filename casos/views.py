from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Cliente, Caso, EstadoCaso, Expediente, Pago


# --- CLIENTES ---
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'casos/cliente_list.html', {'clientes': clientes})

def crear_cliente(request):
    if request.method == 'POST':
        Cliente.objects.create(
            nombres=request.POST.get('nombres'),
            documento=request.POST.get('documento'),
            telefono=request.POST.get('telefono'),
            correo=request.POST.get('correo')
        )
        return redirect('lista_clientes')
    return render(request, 'casos/cliente_form.html')

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, pk=id)
    if request.method == 'POST':
        cliente.nombres = request.POST.get('nombres')
        cliente.documento = request.POST.get('documento')
        cliente.telefono = request.POST.get('telefono')
        cliente.correo = request.POST.get('correo')
        cliente.save()
        return redirect('lista_clientes')
    return render(request, 'casos/cliente_form.html', {'cliente': cliente})

def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, pk=id)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'casos/cliente_confirm_delete.html', {'cliente': cliente})


# --- CASOS Y COOKIES ---
def lista_casos(request):
    estado_id = request.GET.get('estado') or request.COOKIES.get('ultimo_estado')
    casos = Caso.objects.all().select_related('cliente', 'estado').prefetch_related('abogados')

    if estado_id:
        casos = casos.filter(estado_id=estado_id)

    estados = EstadoCaso.objects.all()
    response = render(request, 'casos/caso_list.html', {
        'casos': casos,
        'estados': estados,
        'estado_seleccionado': int(estado_id) if estado_id and estado_id.isdigit() else None
    })

    if request.GET.get('estado'):
        response.set_cookie('ultimo_estado', request.GET.get('estado'), max_age=3600*24*30)

    return response


def detalle_caso(request, id):
    caso = get_object_or_404(Caso, pk=id)
    error_pago = None

    if request.method == 'POST' and 'registrar_pago' in request.POST:
        if not caso.estado.permite_pagos:
            error_pago = f"No se puede registrar el pago: El caso en estado '{caso.estado.nombre}' no admite pagos."
        else:
            monto = request.POST.get('monto')
            descripcion = request.POST.get('descripcion')
            fecha = request.POST.get('fecha')
            if monto and fecha:
                Pago.objects.create(caso=caso, monto=monto, descripcion=descripcion, fecha=fecha)
                return redirect('detalle_caso', id=caso.id)

    return render(request, 'casos/caso_detail.html', {'caso': caso, 'error_pago': error_pago})


def subir_expediente(request, caso_id):
    caso = get_object_or_404(Caso, pk=caso_id)
    if request.method == 'POST':
        Expediente.objects.create(
            caso=caso,
            numero=request.POST.get('numero'),
            juzgado=request.POST.get('juzgado'),
            fecha_presentacion=request.POST.get('fecha_presentacion'),
            documento=request.FILES.get('documento')
        )
    return redirect('detalle_caso', id=caso.id)


def api_caso(request, id):
    caso = get_object_or_404(Caso, pk=id)
    data = {
        'codigo': caso.codigo,
        'titulo': caso.titulo,
        'cliente': caso.cliente.nombres,
        'estado': caso.estado.nombre,
        'abogados': [abog.user.get_full_name() or abog.user.username for abog in caso.abogados.all()],
        'numero_expedientes': caso.expedientes.count(),
        'total_pagado': float(caso.total_pagado())
    }
    return JsonResponse(data)