"""
Tests for automatic audit logging via signals.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from auditing.models import AuditLog
from auditing.signals import set_current_request, clear_current_request
from users.models import Department, Employee
from assets.models import Asset

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_user(
        username="admin_test",
        password="testpass123",
        email="admin@test.com",
        role="ADMIN"
    )


@pytest.fixture
def department(db):
    """Create a test department."""
    return Department.objects.create(name="IT Department")


@pytest.fixture
def request_factory():
    """Fixture for creating mock requests."""
    return RequestFactory()


def create_mock_request(user):
    """Helper to create a mock request with an authenticated user."""
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    return request


@pytest.mark.django_db
class TestAuditSignals:
    """Test automatic audit logging via signals."""

    def test_department_create_audit(self, admin_user):
        """Test that creating a department creates an audit log."""
        # Set current request with authenticated user
        request = create_mock_request(admin_user)
        set_current_request(request)

        # Create a department
        dept = Department.objects.create(name="Finance Department")

        # Check that audit log was created
        audit_logs = AuditLog.objects.filter(
            action='CREATE',
            target_table='users_department',
            target_id=dept.id
        )

        assert audit_logs.exists()
        log = audit_logs.first()
        assert log.system_user == admin_user
        assert log.details['name'] == "Finance Department"

        # Clean up
        clear_current_request()

    def test_department_update_audit(self, admin_user):
        """Test that updating a department creates an audit log."""
        request = create_mock_request(admin_user); set_current_request(request)

        # Create a new department
        department = Department.objects.create(name="Original Name")

        # Clear audit logs from creation
        AuditLog.objects.filter(target_id=department.id).delete()

        # Now update the department
        department.name = "Updated Name"
        department.save()

        # Check that audit log was created
        audit_logs = AuditLog.objects.filter(
            action='UPDATE',
            target_table='users_department',
            target_id=department.id
        )

        assert audit_logs.exists()
        log = audit_logs.first()
        assert log.system_user == admin_user
        assert log.details['name'] == "Updated Name"

        clear_current_request()

    def test_department_delete_audit(self, admin_user, department):
        """Test that deleting a department creates an audit log."""
        request = create_mock_request(admin_user); set_current_request(request)

        dept_id = department.id
        dept_name = department.name

        # Delete the department
        department.delete()

        # Check that audit log was created
        audit_logs = AuditLog.objects.filter(
            action='DELETE',
            target_table='users_department',
            target_id=dept_id
        )

        assert audit_logs.exists()
        log = audit_logs.first()
        assert log.system_user == admin_user
        assert log.details['name'] == dept_name

        clear_current_request()

    def test_asset_create_audit(self, admin_user):
        """Test that creating an asset creates an audit log."""
        request = create_mock_request(admin_user); set_current_request(request)

        # Create an asset
        asset = Asset.objects.create(
            inventory_code="TEST001",
            asset_type="NOTEBOOK",
            brand="Dell",
            model="Latitude 5420",
            status="BODEGA"
        )

        # Check that audit log was created
        audit_logs = AuditLog.objects.filter(
            action='CREATE',
            target_table='assets_asset',
            target_id=asset.id
        )

        assert audit_logs.exists()
        log = audit_logs.first()
        assert log.system_user == admin_user
        assert log.details['inventory_code'] == "TEST001"
        assert log.details['asset_type'] == "NOTEBOOK"

        clear_current_request()

    def test_employee_create_audit(self, admin_user, department):
        """Test that creating an employee creates an audit log."""
        request = create_mock_request(admin_user); set_current_request(request)

        # Create an employee
        employee = Employee.objects.create(
            rut="12345678-9",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            position="Developer",
            department=department
        )

        # Check that audit log was created
        audit_logs = AuditLog.objects.filter(
            action='CREATE',
            target_table='users_employee',
            target_id=employee.id
        )

        assert audit_logs.exists()
        log = audit_logs.first()
        assert log.system_user == admin_user
        assert log.details['rut'] == "12345678-9"
        assert log.details['first_name'] == "John"
        assert log.details['department'] == department.name

        clear_current_request()

    def test_no_audit_without_user(self, department):
        """Test that no audit log is created if no user is set."""
        # Don't set current user
        clear_current_request()

        initial_count = AuditLog.objects.count()

        # Create a department
        Department.objects.create(name="No User Department")

        # Check that no new audit log was created
        assert AuditLog.objects.count() == initial_count

    def test_multiple_operations_audit(self, admin_user, department):
        """Test that multiple operations create multiple audit logs."""
        request = create_mock_request(admin_user); set_current_request(request)

        initial_count = AuditLog.objects.count()

        # Perform multiple operations
        dept2 = Department.objects.create(name="Sales")
        dept2.name = "Sales Department"
        dept2.save()
        dept2.delete()

        # Check that 3 audit logs were created (CREATE, UPDATE, DELETE)
        assert AuditLog.objects.count() == initial_count + 3

        clear_current_request()
