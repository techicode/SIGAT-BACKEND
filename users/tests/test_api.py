import pytest
from rest_framework.test import APIClient
from ..models import Department, CustomUser


@pytest.fixture
def test_user():
    """Create a simple user for autentification tests"""
    return CustomUser.objects.create_user(username="testuser", password="testpassword")


@pytest.mark.django_db
def test_list_departments_authenticated(test_user):
    """
    Test for list the deparments (for authenticated user)
    """

    Department.objects.create(name="Departamento A")
    Department.objects.create(name="Departamento B")

    client = APIClient()
    client.force_authenticate(user=test_user)

    response = client.get("/api/departments/")

    assert response.status_code == 200
    assert len(response.data) == 2

    department_names = [d["name"] for d in response.data]
    assert "Departamento A" in department_names
    assert "Departamento B" in department_names


@pytest.mark.django_db
def test_list_departments_unauthenticated():
    """
    test unaunthenticated user
    """
    client = APIClient()
    response = client.get("/api/departments/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_department_authenticated(test_user):
    """
    test post to create a deparment with a authenticated user
    """
    client = APIClient()
    client.force_authenticate(user=test_user)

    data = {"name": "Nuevo Departamento de TI"}

    response = client.post("/api/departments/", data=data)

    assert response.status_code == 201

    assert response.data["name"] == "Nuevo Departamento de TI"

    assert Department.objects.count() == 1
    assert Department.objects.get().name == "Nuevo Departamento de TI"


@pytest.mark.django_db
def test_create_department_fails_on_duplicate_name_authenticated(test_user):
    """
    Test post to create a duplicated department name with a authenticated user
    """

    Department.objects.create(name="Recursos Humanos")

    client = APIClient()
    client.force_authenticate(user=test_user)

    data = {"name": "Recursos Humanos"}

    response = client.post("/api/departments/", data=data)

    assert response.status_code == 400

    assert Department.objects.count() == 1
