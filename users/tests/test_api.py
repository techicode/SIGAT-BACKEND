import pytest
from rest_framework.test import APIClient
from ..models import Department


@pytest.mark.django_db
def test_list_departments():
    """
    Test for list the deparments
    """

    Department.objects.create(name="Departamento A")
    Department.objects.create(name="Departamento B")

    client = APIClient()
    response = client.get("/api/departments/")

    assert response.status_code == 200
    assert len(response.data) == 2

    department_names = [d["name"] for d in response.data]
    assert "Departamento A" in department_names
    assert "Departamento B" in department_names


@pytest.mark.django_db
def test_create_department():
    """
    test post to create a deparment
    """
    client = APIClient()
    data = {"name": "Nuevo Departamento de TI"}

    response = client.post("/api/departments/", data=data)

    assert response.status_code == 201

    assert response.data["name"] == "Nuevo Departamento de TI"

    assert Department.objects.count() == 1
    assert Department.objects.get().name == "Nuevo Departamento de TI"


@pytest.mark.django_db
def test_create_department_fails_on_duplicate_name():
    """
    Test post to create a duplicated department name
    """

    Department.objects.create(name="Recursos Humanos")

    client = APIClient()
    data = {"name": "Recursos Humanos"}

    response = client.post("/api/departments/", data=data)

    assert response.status_code == 400

    assert Department.objects.count() == 1
