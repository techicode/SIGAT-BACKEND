from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Nombre")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    class RoleChoices(models.TextChoices):
        TECHNICIAN = "TECHNICIAN", "Técnico"
        ADMIN = "ADMIN", "Administrador"

    role = models.CharField(
        max_length=50, choices=RoleChoices.choices, verbose_name="Rol"
    )


class Employee(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    first_name = models.CharField(max_length=150, verbose_name="Nombres")
    last_name = models.CharField(max_length=150, verbose_name="Apellidos")
    email = models.EmailField(max_length=254, unique=True)
    position = models.CharField(max_length=100, blank=True, verbose_name="Cargo")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de Creación"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name="Departamento",
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
