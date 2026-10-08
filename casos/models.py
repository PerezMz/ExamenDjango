from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum


class PerfilAbogado(models.Model):
    """
    Relación OneToOneField con User: Cada usuario abogado tiene un solo perfil.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='perfil'
    )
    numero_colegiatura = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)

    def __str__(self):
        nombre_completo = self.user.get_full_name() or self.user.username
        return f"Abogado: {nombre_completo} - Col: {self.numero_colegiatura}"


class Cliente(models.Model):
    """
    Un cliente puede tener muchos casos.
    """
    nombres = models.CharField(max_length=150)
    documento = models.CharField(max_length=20, unique=True)  # DNI o RUC
    telefono = models.CharField(max_length=20)
    correo = models.EmailField()

    def __str__(self):
        return f"{self.nombres} ({self.documento})"


class EstadoCaso(models.Model):
    """
    Estados del caso. Permite registrar si se autorizan pagos en dicho estado.
    """
    nombre = models.CharField(max_length=50, unique=True)
    permite_pagos = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre


class Caso(models.Model):
    """
    Relaciones:
    - Cliente: ForeignKey (1 a muchos)
    - EstadoCaso: ForeignKey (1 a muchos)
    - PerfilAbogado: ManyToManyField (Muchos a muchos)
    """
    codigo = models.CharField(max_length=20, unique=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateField(auto_now_add=True)
    
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.PROTECT, 
        related_name='casos'
    )
    estado = models.ForeignKey(
        EstadoCaso, 
        on_delete=models.PROTECT, 
        related_name='casos'
    )
    abogados = models.ManyToManyField(
        PerfilAbogado, 
        related_name='casos'
    )

    def __str__(self):
        return f"Caso [{self.codigo}]: {self.titulo}"

    def total_pagado(self):
        """
        Devuelve la suma de todos sus pagos (0 si no tiene pagos), usando aggregate y Sum.
        """
        resultado = self.pagos.aggregate(total=Sum('monto'))['total']
        return resultado if resultado is not None else 0


class Expediente(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='expedientes')
    numero = models.CharField(max_length=50)
    juzgado = models.CharField(max_length=100)
    fecha_presentacion = models.DateField()
    documento = models.FileField(upload_to='expedientes/', null=True, blank=True) # <-- Campo agregado

    def __str__(self):
        return f"Expediente {self.numero} - {self.juzgado}"


class Pago(models.Model):
    """
    Un caso puede tener muchos pagos (1 a muchos).
    """
    caso = models.ForeignKey(
        Caso, 
        on_delete=models.CASCADE, 
        related_name='pagos'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)

    def clean(self):
        """
        Impide registrar un pago si el estado del caso no permite pagos.
        """
        super().clean()
        if self.caso_id and self.caso.estado:
            if not self.caso.estado.permite_pagos:
                raise ValidationError(
                    f"No se pueden registrar pagos para un caso en estado '{self.caso.estado.nombre}'."
                )

    def __str__(self):
        return f"Pago de S/{self.monto} - Caso {self.caso.codigo}"