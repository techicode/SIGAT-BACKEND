import pytest
from django.db import IntegrityError
from ..models import Department, Employee, CustomUser


@pytest.mark.django_db
def test_department_str_representation():
    """
    Test the name of a department
    """

    department = Department.objects.create(name="Facultad de ciencias")

    assert str(department) == "Facultad de ciencias"


@pytest.mark.django_db
def test_department_name_is_unique():
    """
    test duplicated names of department name.
    """

    Department.objects.create(name="Departamento de TI")

    with pytest.raises(IntegrityError):
        Department.objects.create(name="Departamento de TI")


@pytest.mark.django_db
def test_employee_creation_and_relation():
    """
    Test an employee and relation with a department
    """

    dept = Department.objects.create(name="Finanzas")

    employee = Employee.objects.create(
        rut="11.111.111-1",
        first_name="Juan",
        last_name="Pérez",
        email="juan.perez@test.com",
        department=dept,
    )

    assert employee.first_name == "Juan"
    assert employee.department.name == "Finanzas"

    assert dept.employees.count() == 1
    assert str(employee) == "Juan Pérez"


@pytest.mark.django_db
def test_employee_rut_is_unique():
    """
    Test that RUT is unique
    """
    Employee.objects.create(
        rut="22.222.222-2",
        first_name="Ana",
        last_name="Soto",
        email="ana.soto@test.com",
    )
    with pytest.raises(IntegrityError):
        Employee.objects.create(
            rut="22.222.222-2",
            first_name="Clon",
            last_name="De Ana",
            email="clon.ana@test.com",
        )


@pytest.mark.django_db
def test_custom_user_creation():
    """
    Test the custom user created
    """
    user = CustomUser.objects.create_user(
        username="tecnico1",
        password="password123",
        email="tecnico1@test.com",
        first_name="Carlos",
        last_name="Gómez",
        role=CustomUser.RoleChoices.TECHNICIAN,
    )

    assert user.username == "tecnico1"
    assert user.first_name == "Carlos"
    assert user.role == "TECHNICIAN"  # Verificamos nuestro campo personalizado
    assert user.is_staff is False
    assert user.is_superuser is False

    assert user.check_password("password123") is True
    assert user.check_password("wrongpassword") is False


@pytest.mark.django_db
def test_create_superuser():
    """
    The the creation of a superuser
    """
    admin_user = CustomUser.objects.create_superuser(
        username="superadmin", password="password123", email="superadmin@test.com"
    )

    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True
