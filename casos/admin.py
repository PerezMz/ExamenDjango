from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Cliente, EstadoCaso, Caso, Expediente, Pago, PerfilAbogado


# 1. Inline para PerfilAbogado dentro del mantenedor de usuarios
class PerfilAbogadoInline(admin.StackedInline):
    model = PerfilAbogado
    can_delete = False
    verbose_name_plural = 'Perfil de Abogado'


# Personalizamos UserAdmin para incluir el inline
class UserAdmin(BaseUserAdmin):
    inlines = [PerfilAbogadoInline]


# Re-registramos User en el admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# 2. Inlines para CasoAdmin (Expediente y Pago)
class ExpedienteInline(admin.TabularInline):
    model = Expediente
    extra = 1


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1


# 3. ModelAdmin para Cliente
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'documento', 'telefono', 'correo')
    search_fields = ('nombres', 'documento')


# 4. ModelAdmin para EstadoCaso
@admin.register(EstadoCaso)
class EstadoCasoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'permite_pagos')
    list_filter = ('permite_pagos',)


# 5. ModelAdmin para Caso
@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo', 'cliente', 'estado', 'get_total_pagado')
    search_fields = ('codigo', 'titulo', 'cliente__nombres', 'cliente__documento')
    list_filter = ('estado', 'fecha_inicio')
    filter_horizontal = ('abogados',)
    inlines = [ExpedienteInline, PagoInline]

    @admin.display(description='Total Pagado')
    def get_total_pagado(self, obj):
        return f"S/ {obj.total_pagado():.2f}"


# 6. ModelAdmin para Expediente
@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'juzgado', 'fecha_presentacion', 'caso')
    search_fields = ('numero', 'juzgado')
    list_filter = ('fecha_presentacion',)


# Opcional: Registrar Pago si deseas verlo de forma independiente
@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('caso', 'monto', 'fecha', 'descripcion')
    list_filter = ('fecha',)