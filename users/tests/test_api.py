import pytest
from rest_framework.test import APIClient
from ..models import Department, CustomUser


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def technician_user():
    """test user with a technician role"""
    return CustomUser.objects.create_user(
        username="tech", password="pw", role=CustomUser.RoleChoices.TECHNICIAN
    )


@pytest.fixture
def admin_user():
    """test user with a admin role"""
    return CustomUser.objects.create_user(
        username="admin", password="pw", role=CustomUser.RoleChoices.ADMIN
    )


@pytest.mark.django_db
def test_list_departments_technician(api_client, technician_user):
    """
    Test for list the deparments (for authenticated user)
    """

    Department.objects.create(name="Departamento A")
    Department.objects.create(name="Departamento B")

    api_client.force_authenticate(user=technician_user)

    response = api_client.get("/api/departments/")

    assert response.status_code == 200
    assert len(response.data['results']) == 2

    department_names = [d["name"] for d in response.data['results']]
    assert "Departamento A" in department_names
    assert "Departamento B" in department_names


@pytest.mark.django_db
def test_create_department_as_technician_fails(api_client, technician_user):
    """
    test for technician, cannot create a deparment
    """

    api_client.force_authenticate(user=technician_user)

    data = {"name": "Departamento Prohibido"}
    response = api_client.post("/api/departments/", data=data)

    assert response.status_code == 403


@pytest.mark.django_db
def test_list_departments_unauthenticated(api_client):
    """
    test unaunthenticated user
    """

    response = api_client.get("/api/departments/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_create_department_as_admin_succeeds(api_client, admin_user):
    """
    test for an admin can create a deparment
    """

    api_client.force_authenticate(user=admin_user)

    data = {"name": "Departamento Permitido"}
    response = api_client.post("/api/departments/", data=data)

    assert response.status_code == 201
    assert Department.objects.count() == 1


@pytest.mark.django_db
def test_create_department_fails_on_duplicate_name(api_client, admin_user):
    """
    Test post to create a duplicated department name with a authenticated user
    """
    Department.objects.create(name="Recursos Humanos")

    api_client.force_authenticate(user=admin_user)

    data = {"name": "Recursos Humanos"}

    response = api_client.post("/api/departments/", data=data)

    assert response.status_code == 400

    assert Department.objects.count() == 1
