from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _


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

    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="customuser_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="customuser_set",
        related_query_name="user",
    )

    def save(self, *args, **kwargs):
        if self.role == self.RoleChoices.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)


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
