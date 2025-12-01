"""
Django signals for automatic audit logging.

This module captures all CREATE, UPDATE, and DELETE operations on critical models
and automatically creates AuditLog entries.
"""
import logging
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from threading import local

logger = logging.getLogger(__name__)

# Thread-local storage for current request
_thread_locals = local()


def get_current_user():
    """Get the current user from the stored request in thread-local storage."""
    request = getattr(_thread_locals, 'request', None)

    if request is None:
        logger.debug(f"[AUDIT SIGNALS] No request in thread-local")
        return None

    if not hasattr(request, 'user'):
        logger.debug(f"[AUDIT SIGNALS] Request has no user attribute")
        return None

    user = request.user if request.user.is_authenticated else None
    logger.info(f"[AUDIT SIGNALS] get_current_user() from request returning: {user}")
    return user


def set_current_request(request):
    """Set the current request in thread-local storage."""
    _thread_locals.request = request
    logger.debug(f"[AUDIT SIGNALS] set_current_request() called for {request.method} {request.path}")


def clear_current_request():
    """Clear the current request from thread-local storage."""
    if hasattr(_thread_locals, 'request'):
        logger.debug(f"[AUDIT SIGNALS] Clearing current request")
        delattr(_thread_locals, 'request')


def save_old_instance(instance):
    """
    Save the old state of an instance before it's updated.
    Used in pre_save signals to capture what's about to change.
    """
    key = f"old_instance_{instance.__class__.__name__}_{instance.pk}"

    # Only save if this is an update (pk exists)
    if instance.pk:
        try:
            old_instance = instance.__class__.objects.get(pk=instance.pk)
            _thread_locals.__dict__[key] = old_instance
            logger.debug(f"[AUDIT SIGNALS] Saved old instance for {instance.__class__.__name__} pk={instance.pk}")
        except instance.__class__.DoesNotExist:
            logger.debug(f"[AUDIT SIGNALS] No old instance found for {instance.__class__.__name__} pk={instance.pk}")


def get_instance_changes(instance):
    """
    Get the changes between the old instance (saved in pre_save) and current instance.
    Returns a dict of {field_name: {'old': old_value, 'new': new_value}}
    """
    key = f"old_instance_{instance.__class__.__name__}_{instance.pk}"
    old_instance = _thread_locals.__dict__.get(key)

    if not old_instance:
        logger.debug(f"[AUDIT SIGNALS] No old instance to compare for {instance.__class__.__name__}")
        return None

    changes = {}
    for field in instance._meta.fields:
        # Skip auto fields and relations that might cause issues
        if field.auto_created:
            continue

        field_name = field.name
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(instance, field_name, None)

        # Convert to string for comparison (handles dates, foreign keys, etc.)
        old_str = str(old_value) if old_value is not None else None
        new_str = str(new_value) if new_value is not None else None

        if old_str != new_str:
            changes[field_name] = {
                'old': old_str,
                'new': new_str
            }

    # Clean up the stored old instance
    if key in _thread_locals.__dict__:
        del _thread_locals.__dict__[key]

    logger.info(f"[AUDIT SIGNALS] Detected {len(changes)} changes for {instance.__class__.__name__}: {list(changes.keys())}")
    return changes if changes else None


# Import models after defining thread-local functions to avoid circular imports
from .models import AuditLog
from assets.models import Asset, ComputerDetail, StorageDevice, GraphicsCard
from users.models import Department, Employee
from software.models import SoftwareCatalog, License, InstalledSoftware, Vulnerability
from .models import ComplianceWarning, AssetCheckin

User = get_user_model()


def create_audit_log(action, instance, details=None):
    """
    Helper function to create audit log entries.

    Args:
        action: One of CREATE, UPDATE, DELETE
        instance: The model instance being modified
        details: Optional dict with additional details
    """
    user = get_current_user()

    # Get table name for logging
    table_name = f"{instance._meta.app_label}_{instance._meta.model_name}"

    logger.info(f"[AUDIT SIGNALS] create_audit_log called: action={action}, table={table_name}, id={instance.pk}, user={user}")

    # If no user in thread local, skip audit (e.g., system operations, migrations, etc.)
    if not user or not user.is_authenticated:
        logger.warning(f"[AUDIT SIGNALS] Skipping audit log - no authenticated user (user={user})")
        return

    try:
        # Create the audit log
        audit_log = AuditLog.objects.create(
            system_user=user,
            action=action,
            target_table=table_name,
            target_id=instance.pk,
            details=details or {}
        )
        logger.info(f"[AUDIT SIGNALS] ✓ Audit log created: ID={audit_log.id}, user={user.username}, action={action}, table={table_name}")
    except Exception as e:
        logger.error(f"[AUDIT SIGNALS] ✗ Failed to create audit log: {e}", exc_info=True)


def get_model_diff(instance):
    """
    Get changed fields from a model instance.
    Only works on UPDATE operations.
    """
    if not instance.pk:
        return None

    try:
        # Get the old version from database
        old_instance = instance.__class__.objects.get(pk=instance.pk)

        # Compare fields
        changes = {}
        for field in instance._meta.fields:
            field_name = field.name
            old_value = getattr(old_instance, field_name, None)
            new_value = getattr(instance, field_name, None)

            # Convert to string for comparison (handles dates, foreign keys, etc.)
            old_str = str(old_value) if old_value is not None else None
            new_str = str(new_value) if new_value is not None else None

            if old_str != new_str:
                changes[field_name] = {
                    'old': old_str,
                    'new': new_str
                }

        return changes if changes else None
    except instance.__class__.DoesNotExist:
        return None


def get_instance_details(instance):
    """
    Get basic details about an instance for CREATE/DELETE operations.
    """
    details = {}

    # Add string representation
    details['str_representation'] = str(instance)

    # Add key fields based on model type
    if hasattr(instance, 'inventory_code'):
        details['inventory_code'] = instance.inventory_code
    if hasattr(instance, 'rut'):
        details['rut'] = instance.rut
    if hasattr(instance, 'name'):
        details['name'] = instance.name
    if hasattr(instance, 'username'):
        details['username'] = instance.username
    if hasattr(instance, 'email'):
        details['email'] = instance.email

    return details


# =============================================================================
# ASSET MODELS
# =============================================================================

@receiver(pre_save, sender=Asset)
def asset_pre_save(sender, instance, **kwargs):
    """Capture the old state before saving."""
    save_old_instance(instance)


@receiver(post_save, sender=Asset)
def audit_asset_save(sender, instance, created, **kwargs):
    """Audit Asset creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    logger.info(f"[AUDIT SIGNALS] Asset signal fired: action={action}, inventory_code={instance.inventory_code}")

    if created:
        # For CREATE, save basic info
        details = {
            'inventory_code': instance.inventory_code,
            'asset_type': instance.asset_type,
            'brand': instance.brand,
            'model': instance.model,
            'status': instance.status,
        }
    else:
        # For UPDATE, only save what changed
        changes = get_instance_changes(instance)
        if not changes:
            logger.info(f"[AUDIT SIGNALS] No changes detected for Asset {instance.inventory_code}, skipping audit")
            return

        details = {
            'inventory_code': instance.inventory_code,
            'changes': changes
        }

    create_audit_log(action=action, instance=instance, details=details)


@receiver(pre_delete, sender=Asset)
def audit_asset_delete(sender, instance, **kwargs):
    """Audit Asset deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'inventory_code': instance.inventory_code,
            'asset_type': instance.asset_type,
            'brand': instance.brand,
            'model': instance.model,
        }
    )


@receiver(post_save, sender=ComputerDetail)
def audit_computer_detail_save(sender, instance, created, **kwargs):
    """Audit ComputerDetail creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    create_audit_log(
        action=action,
        instance=instance,
        details={
            'asset_inventory_code': instance.asset.inventory_code if instance.asset else None,
            'cpu_model': instance.cpu_model,
            'ram_gb': str(instance.ram_gb) if instance.ram_gb else None,
        }
    )


@receiver(pre_delete, sender=ComputerDetail)
def audit_computer_detail_delete(sender, instance, **kwargs):
    """Audit ComputerDetail deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'asset_inventory_code': instance.asset.inventory_code if instance.asset else None,
        }
    )


# =============================================================================
# USER MODELS
# =============================================================================

@receiver(pre_save, sender=Employee)
def employee_pre_save(sender, instance, **kwargs):
    """Capture the old state before saving."""
    save_old_instance(instance)


@receiver(post_save, sender=Employee)
def audit_employee_save(sender, instance, created, **kwargs):
    """Audit Employee creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    logger.info(f"[AUDIT SIGNALS] Employee signal fired: action={action}, id={instance.id}, rut={instance.rut}")

    if created:
        # For CREATE, save basic info
        details = {
            'rut': instance.rut,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'email': instance.email,
            'department': instance.department.name if instance.department else None,
        }
    else:
        # For UPDATE, only save what changed
        changes = get_instance_changes(instance)
        if not changes:
            logger.info(f"[AUDIT SIGNALS] No changes detected for Employee {instance.rut}, skipping audit")
            return

        details = {
            'rut': instance.rut,
            'changes': changes
        }

    create_audit_log(action=action, instance=instance, details=details)


@receiver(pre_delete, sender=Employee)
def audit_employee_delete(sender, instance, **kwargs):
    """Audit Employee deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'rut': instance.rut,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'email': instance.email,
        }
    )


@receiver(pre_save, sender=Department)
def department_pre_save(sender, instance, **kwargs):
    """Capture the old state before saving."""
    save_old_instance(instance)


@receiver(post_save, sender=Department)
def audit_department_save(sender, instance, created, **kwargs):
    """Audit Department creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    logger.info(f"[AUDIT SIGNALS] Department signal fired: action={action}, id={instance.id}, name={instance.name}")

    if created:
        # For CREATE, save basic info
        details = {'name': instance.name}
    else:
        # For UPDATE, only save what changed
        changes = get_instance_changes(instance)
        if not changes:
            logger.info(f"[AUDIT SIGNALS] No changes detected for Department {instance.name}, skipping audit")
            return

        details = {
            'name': instance.name,
            'changes': changes
        }

    create_audit_log(action=action, instance=instance, details=details)


@receiver(pre_delete, sender=Department)
def audit_department_delete(sender, instance, **kwargs):
    """Audit Department deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={'name': instance.name}
    )


@receiver(post_save, sender=User)
def audit_user_save(sender, instance, created, **kwargs):
    """Audit CustomUser creation and updates."""
    # Skip audit for password changes (security)
    if not created and 'password' in kwargs.get('update_fields', []):
        return

    if created:
        create_audit_log(
            action='CREATE',
            instance=instance,
            details={
                'username': instance.username,
                'email': instance.email,
                'role': instance.role,
                'is_active': instance.is_active,
            }
        )
    else:
        changes = get_model_diff(instance)
        if changes:
            # Remove password from changes
            changes.pop('password', None)
            if changes:
                create_audit_log(
                    action='UPDATE',
                    instance=instance,
                    details={
                        'username': instance.username,
                        'changes': changes
                    }
                )


@receiver(pre_delete, sender=User)
def audit_user_delete(sender, instance, **kwargs):
    """Audit CustomUser deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'username': instance.username,
            'email': instance.email,
            'role': instance.role,
        }
    )


# =============================================================================
# SOFTWARE MODELS
# =============================================================================

@receiver(post_save, sender=SoftwareCatalog)
def audit_software_save(sender, instance, created, **kwargs):
    """Audit SoftwareCatalog creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    details = {
        'name': instance.name,
        'developer': instance.developer,
    }

    if not created:
        changes = get_model_diff(instance)
        if changes:
            details['changes'] = changes

    create_audit_log(action=action, instance=instance, details=details)


@receiver(pre_delete, sender=SoftwareCatalog)
def audit_software_delete(sender, instance, **kwargs):
    """Audit SoftwareCatalog deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'name': instance.name,
            'developer': instance.developer,
        }
    )


@receiver(post_save, sender=License)
def audit_license_save(sender, instance, created, **kwargs):
    """Audit License creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    details = {
        'software': instance.software.name if instance.software else None,
        'quantity': instance.quantity,
        'purchase_date': instance.purchase_date.isoformat() if instance.purchase_date else None,
        'expiration_date': instance.expiration_date.isoformat() if instance.expiration_date else None,
        # Don't log the actual license key for security
        'has_license_key': bool(instance.license_key),
    }

    if not created:
        changes = get_model_diff(instance)
        if changes:
            # Remove license_key from changes for security
            changes.pop('license_key', None)
            if changes:
                details['changes'] = changes

    create_audit_log(action=action, instance=instance, details=details)


@receiver(pre_delete, sender=License)
def audit_license_delete(sender, instance, **kwargs):
    """Audit License deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'software': instance.software.name if instance.software else None,
            'quantity': instance.quantity,
        }
    )


@receiver(post_save, sender=InstalledSoftware)
def audit_installed_software_save(sender, instance, created, **kwargs):
    """Audit InstalledSoftware creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    create_audit_log(
        action=action,
        instance=instance,
        details={
            'asset': instance.asset.inventory_code if instance.asset else None,
            'software': instance.software.name if instance.software else None,
            'license': instance.license.id if instance.license else None,
        }
    )


@receiver(pre_delete, sender=InstalledSoftware)
def audit_installed_software_delete(sender, instance, **kwargs):
    """Audit InstalledSoftware deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'asset': instance.asset.inventory_code if instance.asset else None,
            'software': instance.software.name if instance.software else None,
        }
    )


# =============================================================================
# AUDITING MODELS
# =============================================================================

@receiver(pre_save, sender=ComplianceWarning)
def compliance_warning_pre_save(sender, instance, **kwargs):
    """Capture the old state before saving."""
    save_old_instance(instance)


@receiver(post_save, sender=ComplianceWarning)
def audit_compliance_warning_save(sender, instance, created, **kwargs):
    """Audit ComplianceWarning creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    logger.info(f"[AUDIT SIGNALS] ComplianceWarning signal fired: action={action}, id={instance.id}")

    if created:
        # For CREATE, save basic info
        details = {
            'asset': instance.asset.inventory_code if instance.asset else None,
            'category': instance.category,
            'status': instance.status,
            'description': instance.description,
        }
    else:
        # For UPDATE, only save what changed
        changes = get_instance_changes(instance)
        if not changes:
            logger.info(f"[AUDIT SIGNALS] No changes detected for ComplianceWarning {instance.id}, skipping audit")
            return

        details = {
            'asset': instance.asset.inventory_code if instance.asset else None,
            'category': instance.category,
            'changes': changes
        }

    create_audit_log(action=action, instance=instance, details=details)


@receiver(pre_delete, sender=ComplianceWarning)
def audit_compliance_warning_delete(sender, instance, **kwargs):
    """Audit ComplianceWarning deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'asset': instance.asset.inventory_code if instance.asset else None,
            'category': instance.category,
            'status': instance.status,
        }
    )


@receiver(post_save, sender=AssetCheckin)
def audit_asset_checkin_save(sender, instance, created, **kwargs):
    """Audit AssetCheckin creation and updates."""
    action = 'CREATE' if created else 'UPDATE'
    create_audit_log(
        action=action,
        instance=instance,
        details={
            'asset': instance.asset.inventory_code if instance.asset else None,
            'employee': instance.employee.rut if instance.employee else None,
            'physical_state': instance.physical_state,
        }
    )


@receiver(pre_delete, sender=AssetCheckin)
def audit_asset_checkin_delete(sender, instance, **kwargs):
    """Audit AssetCheckin deletion."""
    create_audit_log(
        action='DELETE',
        instance=instance,
        details={
            'asset': instance.asset.inventory_code if instance.asset else None,
            'employee': instance.employee.rut if instance.employee else None,
        }
    )
