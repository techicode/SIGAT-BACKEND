"""
Database seeding script for SIGAT.
Run with: python manage.py runscript seed_data
"""

import random
from faker import Faker

from assets.models import Asset, ComputerDetail, StorageDevice, GraphicsCard
from auditing.models import AuditLog, AssetCheckin, ComplianceWarning
from software.models import SoftwareCatalog, InstalledSoftware, License
from users.models import CustomUser, Department, Employee


# Initialize Faker with Spanish locale
fake = Faker('es_ES')


def run():
    """Main function that executes database seeding."""

    print("=" * 80)
    print("STARTING SIGAT DATABASE SEEDING")
    print("=" * 80)

    # Step 1: Clear existing data
    print("\n[1/9] Clearing existing data...")
    clear_database()

    # Step 2: Create users
    print("\n[2/9] Creating system users...")
    users = create_users()
    print(f"✓ {len(users)} users created (5 technicians, 2 admins)")

    # Step 3: Create base entities
    print("\n[3/9] Creating departments...")
    departments = create_departments()
    print(f"✓ {len(departments)} departments created")

    print("\n[4/9] Creating software catalog...")
    software_catalog = create_software_catalog()
    print(f"✓ {len(software_catalog)} software applications created")

    print("\n[5/9] Creating employees...")
    employees = create_employees(departments)
    print(f"✓ {len(employees)} employees created")

    # Step 6: Create assets and relationships
    print("\n[6/9] Creating assets with hardware and software details...")
    assets = Asset.objects.all()  # We'll need to get these after creation
    total_assets = create_assets(departments, employees, software_catalog)

    # Refresh assets list
    assets = list(Asset.objects.all())

    # Step 7: Create auditing records
    print("\n[7/9] Creating asset check-ins...")
    total_checkins = create_asset_checkins(assets, employees)

    print("\n[8/9] Creating compliance warnings...")
    total_warnings = create_compliance_warnings(assets, users)

    print("\n[9/9] Creating audit logs...")
    total_logs = create_audit_logs(users, assets)

    # Final summary
    print("\n" + "=" * 80)
    print("SEEDING COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"Total users: {len(users)}")
    print(f"Total departments: {len(departments)}")
    print(f"Total employees: {len(employees)}")
    print(f"Total software in catalog: {len(software_catalog)}")
    print(f"Total assets created: {total_assets}")
    print(f"Total asset check-ins: {total_checkins}")
    print(f"Total compliance warnings: {total_warnings}")
    print(f"Total audit logs: {total_logs}")
    print("=" * 80)


def clear_database():
    """Delete all existing records from main models."""

    # Deletion order respecting dependencies
    models_to_clear = [
        ('Asset Checkins', AssetCheckin),
        ('Compliance Warnings', ComplianceWarning),
        ('Audit Logs', AuditLog),
        ('Installed Software', InstalledSoftware),
        ('Licenses', License),
        ('Software Catalog', SoftwareCatalog),
        ('Storage Devices', StorageDevice),
        ('Graphics Cards', GraphicsCard),
        ('Computer Details', ComputerDetail),
        ('Assets', Asset),
        ('Employees', Employee),
        ('Departments', Department),
        ('Users', CustomUser),
    ]

    for name, model in models_to_clear:
        count = model.objects.count()
        if count > 0:
            model.objects.all().delete()
            print(f"  - {name}: {count} records deleted")


def create_departments():
    """Create university departments."""

    department_names = [
        "Facultad de Ingeniería",
        "Facultad de Ciencias de la Salud",
        "Biblioteca Central",
        "Departamento de Finanzas",
        "Dirección de Tecnologías de Información",
        "Facultad de Educación",
        "Recursos Humanos",
    ]

    departments = []
    for name in department_names:
        dept = Department.objects.create(name=name)
        departments.append(dept)
        print(f"  - {name}")

    return departments


def create_users():
    """Create technician and admin users."""

    users = []
    used_usernames = set()

    # Create 5 technicians
    print("  Creating technicians...")
    for i in range(5):
        # Generate unique username
        while True:
            first = fake.first_name().lower()
            last = fake.last_name().lower()
            username = f"{first}.{last}"
            if username not in used_usernames:
                used_usernames.add(username)
                break

        user = CustomUser.objects.create_user(
            username=username,
            password='password123',
            email=f"{username}@universidad.cl",
            role=CustomUser.RoleChoices.TECHNICIAN,
            is_active=True
        )
        users.append(user)
        print(f"    - Technician: {username}")

    # Create 2 admins
    print("  Creating administrators...")
    for i in range(2):
        # Generate unique username
        while True:
            first = fake.first_name().lower()
            last = fake.last_name().lower()
            username = f"{first}.{last}.admin"
            if username not in used_usernames:
                used_usernames.add(username)
                break

        user = CustomUser.objects.create_user(
            username=username,
            password='password123',
            email=f"{username}@universidad.cl",
            role=CustomUser.RoleChoices.ADMIN,
            is_active=True
        )
        users.append(user)
        print(f"    - Admin: {username}")

    return users


def create_software_catalog():
    """Create software catalog with common applications."""

    software_data = [
        ("Microsoft Office 365", "Microsoft"),
        ("Google Chrome", "Google"),
        ("Mozilla Firefox", "Mozilla Foundation"),
        ("Adobe Acrobat Reader", "Adobe"),
        ("AutoCAD", "Autodesk"),
        ("7-Zip", "Igor Pavlov"),
        ("VLC Media Player", "VideoLAN"),
        ("Python", "Python Software Foundation"),
        ("Visual Studio Code", "Microsoft"),
        ("Slack", "Slack Technologies"),
        ("Zoom", "Zoom Video Communications"),
        ("WinRAR", "RARLAB"),
        ("Notepad++", "Don Ho"),
        ("Git", "Software Freedom Conservancy"),
        ("LibreOffice", "The Document Foundation"),
    ]

    catalog = []
    for name, developer in software_data:
        software = SoftwareCatalog.objects.create(
            name=name,
            developer=developer
        )
        catalog.append(software)
        print(f"  - {name} ({developer})")

    return catalog


def generate_rut():
    """Generate a Chilean RUT with format XX.XXX.XXX-X."""

    # Generate base number (7-8 digits)
    number = random.randint(10000000, 25999999)

    # Calculate verification digit
    reversed_digits = map(int, reversed(str(number)))
    factors = [2, 3, 4, 5, 6, 7]
    s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    verifier = 11 - (s % 11)

    if verifier == 11:
        verifier = '0'
    elif verifier == 10:
        verifier = 'K'
    else:
        verifier = str(verifier)

    # Format RUT
    rut_str = str(number)
    formatted_rut = f"{rut_str[:-6]}.{rut_str[-6:-3]}.{rut_str[-3:]}-{verifier}"

    return formatted_rut


def create_employees(departments):
    """Create employees with realistic data using Faker."""

    employees = []
    used_ruts = set()
    used_emails = set()

    positions = [
        "Profesor", "Investigador", "Asistente Administrativo",
        "Coordinador", "Técnico", "Analista", "Jefe de Departamento",
        "Bibliotecario", "Contador", "Desarrollador"
    ]

    for i in range(25):
        # Generate unique RUT
        while True:
            rut = generate_rut()
            if rut not in used_ruts:
                used_ruts.add(rut)
                break

        # Generate unique email
        while True:
            email = fake.email()
            if email not in used_emails:
                used_emails.add(email)
                break

        employee = Employee.objects.create(
            rut=rut,
            first_name=fake.first_name(),
            last_name=f"{fake.last_name()} {fake.last_name()}",
            email=email,
            position=random.choice(positions),
            department=random.choice(departments)
        )
        employees.append(employee)

        if (i + 1) % 5 == 0:
            print(f"  - {i + 1} employees created...")

    return employees


def create_assets(departments, employees, software_catalog):
    """Create assets with their hardware and installed software details."""

    TOTAL_ASSETS = 150
    created_count = 0

    # Lists for generating realistic data
    notebook_brands = ["Dell", "HP", "Lenovo", "Asus", "Acer", "Apple"]
    desktop_brands = ["Dell", "HP", "Lenovo", "Asus"]

    cpu_models = [
        "Intel Core i5-10400",
        "Intel Core i7-9750H",
        "Intel Core i5-1135G7",
        "AMD Ryzen 5 5600X",
        "AMD Ryzen 7 5800H",
        "Intel Core i7-11800H",
    ]

    operating_systems = [
        ("Microsoft Windows 11 Pro", "10.0.22621", "AMD64"),
        ("Microsoft Windows 10 Pro", "10.0.19045", "AMD64"),
        ("Microsoft Windows 11 Home", "10.0.22000", "AMD64"),
        ("Ubuntu Linux", "22.04", "x86_64"),
    ]

    motherboard_manufacturers = ["Dell Inc.", "HP", "ASUS", "Gigabyte", "MSI", "Lenovo"]

    storage_models = [
        "Samsung SSD 970 EVO Plus",
        "Kingston A400 SSD",
        "WD Blue",
        "Seagate Barracuda",
        "Crucial MX500",
        "Samsung 860 EVO",
    ]

    gpu_models = [
        "Intel UHD Graphics 630",
        "NVIDIA GeForce GTX 1650",
        "AMD Radeon RX 580",
        "NVIDIA GeForce RTX 3060",
        "Intel Iris Xe Graphics",
    ]

    for i in range(TOTAL_ASSETS):
        # Determine asset type (only NOTEBOOK or DESKTOP as per requirements)
        asset_type = random.choice([
            Asset.AssetTypeChoices.NOTEBOOK,
            Asset.AssetTypeChoices.DESKTOP
        ])

        # Generate inventory code with format UPLA-TYPE-NNNN
        type_code = "NOTE" if asset_type == Asset.AssetTypeChoices.NOTEBOOK else "DESK"
        inventory_code = f"UPLA-{type_code}-{i+1:04d}"

        # Generate unique serial number
        serial_number = fake.bothify(text='??########').upper()

        # Select brand based on type
        if asset_type == Asset.AssetTypeChoices.NOTEBOOK:
            brand = random.choice(notebook_brands)
        else:
            brand = random.choice(desktop_brands)

        # Select random status
        status = random.choice([
            Asset.StatusChoices.IN_STORAGE,
            Asset.StatusChoices.ASSIGNED,
            Asset.StatusChoices.IN_REPAIR,
            Asset.StatusChoices.DISPOSED,
        ])

        # Assign employee only if status is ASSIGNED
        assigned_employee = None
        if status == Asset.StatusChoices.ASSIGNED:
            assigned_employee = random.choice(employees)

        # Acquisition date (last 3 years)
        acquisition_date = fake.date_between(start_date='-3y', end_date='today')

        # Create the asset
        asset = Asset.objects.create(
            inventory_code=inventory_code,
            serial_number=serial_number,
            asset_type=asset_type,
            status=status,
            brand=brand,
            model=fake.bothify(text='Model-####'),
            acquisition_date=acquisition_date,
            employee=assigned_employee,
            department=random.choice(departments)
        )

        # Create associated ComputerDetail
        os_name, os_version, os_arch = random.choice(operating_systems)
        ComputerDetail.objects.create(
            asset=asset,
            unique_identifier=fake.uuid4(),
            os_name=os_name,
            os_version=os_version,
            os_arch=os_arch,
            cpu_model=random.choice(cpu_models),
            ram_gb=random.choice([4, 8, 16, 32]),
            motherboard_manufacturer=random.choice(motherboard_manufacturers),
            motherboard_model=fake.bothify(text='MB-####'),
            last_updated_by_agent=None
        )

        # Create at least one StorageDevice
        primary_capacity = random.choice([256, 512, 1024, 2048])
        free_space = primary_capacity * random.uniform(0.2, 0.7)

        StorageDevice.objects.create(
            asset=asset,
            model=random.choice(storage_models),
            serial_number=fake.bothify(text='S??########').upper(),
            capacity_gb=primary_capacity,
            free_space_gb=round(free_space, 2)
        )

        # 50% chance of having a second disk
        if random.random() < 0.5:
            secondary_capacity = random.choice([512, 1024, 2048])
            secondary_free_space = secondary_capacity * random.uniform(0.3, 0.8)

            StorageDevice.objects.create(
                asset=asset,
                model=random.choice(storage_models),
                serial_number=fake.bothify(text='S??########').upper(),
                capacity_gb=secondary_capacity,
                free_space_gb=round(secondary_free_space, 2)
            )

        # Create GraphicsCard (optional, 70% probability)
        if random.random() < 0.7:
            GraphicsCard.objects.create(
                asset=asset,
                model_name=random.choice(gpu_models)
            )

        # Install between 2 and 5 software programs (no duplicates)
        software_count = random.randint(2, 5)
        selected_software = random.sample(software_catalog, software_count)

        for software in selected_software:
            InstalledSoftware.objects.create(
                asset=asset,
                software=software,
                version=f"{random.randint(1, 20)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
                install_date=fake.date_between(
                    start_date=acquisition_date,
                    end_date='today'
                ),
                license=None  # No license assignment in this basic seed
            )

        created_count += 1

        # Show progress every 25 assets
        if created_count % 25 == 0:
            print(f"  - {created_count}/{TOTAL_ASSETS} assets created...")

    print(f"  - {created_count}/{TOTAL_ASSETS} assets created... Completed!")
    return created_count


def create_asset_checkins(assets, employees):
    """Create asset check-ins for assigned assets."""

    TARGET_CHECKINS = 25
    physical_states = ["Nuevo", "Muy Bueno", "Bueno", "Aceptable", "Necesita Reparación"]

    # Sample notes that may appear in check-ins
    sample_notes = [
        "Todo funciona correctamente.",
        "La batería ha perdido algo de duración.",
        "El equipo está en excelente estado.",
        "Se escucha el ventilador con frecuencia.",
        "Pantalla con algún rayón menor.",
        "Teclado presenta desgaste en algunas teclas.",
        "Funciona bien pero es un poco lento al iniciar.",
        "Sin problemas reportados.",
        "El touchpad a veces no responde bien.",
        "Necesita limpieza de polvo.",
    ]

    # Get only assets that are ASSIGNED (have an employee)
    assigned_assets = [a for a in assets if a.status == Asset.StatusChoices.ASSIGNED and a.employee]

    if not assigned_assets:
        print("  No assigned assets found. Skipping check-ins.")
        return 0

    checkins_created = 0

    # Distribute check-ins across assigned assets
    # Some assets may have multiple historical check-ins
    while checkins_created < TARGET_CHECKINS and assigned_assets:
        asset = random.choice(assigned_assets)

        # Create check-in for this asset
        checkin_date = fake.date_time_between(start_date='-6M', end_date='now')

        AssetCheckin.objects.create(
            asset=asset,
            employee=asset.employee,
            checkin_date=checkin_date,
            physical_state=random.choice(physical_states),
            performance_satisfaction=random.randint(1, 5),
            notes=random.choice(sample_notes) if random.random() < 0.5 else ""
        )

        checkins_created += 1

        if checkins_created % 10 == 0:
            print(f"  - {checkins_created}/{TARGET_CHECKINS} check-ins created...")

    print(f"  - {checkins_created}/{TARGET_CHECKINS} check-ins created... Completed!")
    return checkins_created


def create_compliance_warnings(assets, users):
    """Create compliance warnings for assets with detected issues."""

    TARGET_WARNINGS = 25

    # Pirated software names and typical installation paths
    pirated_software_paths = [
        "C:\\Program Files\\Adobe Photoshop CC 2023\\crack.exe",
        "C:\\Games\\FIFA 24\\keygen.exe",
        "C:\\Program Files\\Autodesk\\AutoCAD 2024\\xforce.dll",
        "C:\\Users\\Public\\Downloads\\Office_Crack.exe",
        "C:\\Games\\GTA V\\crack\\patch.exe",
        "C:\\Software\\CorelDRAW\\keygen.exe",
        "C:\\Program Files (x86)\\Nero\\crack.dll",
        "C:\\Downloads\\Windows_Activator.exe",
        "D:\\Games\\Minecraft Premium\\launcher_crack.exe",
        "C:\\Adobe\\Premiere Pro 2023\\AMTEmu.exe",
        "C:\\Archivos\\Programas crackeados\\winrar_keygen.exe",
        "C:\\Games\\Sims 4\\crack_v2.exe",
    ]

    # Get only computer assets (NOTEBOOK or DESKTOP)
    computer_assets = [
        a for a in assets
        if a.asset_type in [Asset.AssetTypeChoices.NOTEBOOK, Asset.AssetTypeChoices.DESKTOP]
    ]

    if not computer_assets:
        print("  No computer assets found. Skipping compliance warnings.")
        return 0

    # Calculate distribution
    # 50% RESOLVED, 30% NEW, 10% IN_REVIEW, 10% FALSE_POSITIVE
    resolved_count = int(TARGET_WARNINGS * 0.5)  # 12-13
    new_count = int(TARGET_WARNINGS * 0.3)  # 7-8
    in_review_count = int(TARGET_WARNINGS * 0.1)  # 2-3
    false_positive_count = TARGET_WARNINGS - resolved_count - new_count - in_review_count  # remainder

    statuses_distribution = (
        [ComplianceWarning.StatusChoices.RESOLVED] * resolved_count +
        [ComplianceWarning.StatusChoices.NEW] * new_count +
        [ComplianceWarning.StatusChoices.IN_REVIEW] * in_review_count +
        [ComplianceWarning.StatusChoices.FALSE_POSITIVE] * false_positive_count
    )

    # Resolution notes samples for different statuses
    resolution_notes_samples = {
        ComplianceWarning.StatusChoices.RESOLVED: [
            "Software eliminado. Se instaló versión con licencia válida.",
            "Archivo crackeado removido del sistema. Usuario capacitado sobre políticas de software.",
            "Se desinstaló el software no autorizado. Licencia corporativa adquirida e instalada.",
            "Crack eliminado. Se verificó instalación de versión legítima.",
        ],
        ComplianceWarning.StatusChoices.IN_REVIEW: [
            "Revisando con el usuario. Pendiente verificación de licencia.",
            "En proceso de análisis. Coordinando con departamento legal.",
            "Verificando si el software es necesario para las funciones del empleado.",
        ],
        ComplianceWarning.StatusChoices.FALSE_POSITIVE: [
            "Falsa alarma. El archivo es parte de un software legítimo.",
            "Error del agente. El ejecutable es una herramienta de desarrollo autorizada.",
            "No es software pirata. Se trata de un parche oficial del fabricante.",
        ],
    }

    warnings_created = 0

    for status in statuses_distribution:
        asset = random.choice(computer_assets)

        # Generate 1-3 evidence paths
        num_paths = random.randint(1, 3)
        evidence_paths = random.sample(pirated_software_paths, num_paths)
        evidence = {"paths": evidence_paths}

        # Determine if we need resolved_by and resolution_notes
        resolved_by = None
        resolution_notes = ""

        if status != ComplianceWarning.StatusChoices.NEW:
            resolved_by = random.choice(users)
            if status in resolution_notes_samples:
                resolution_notes = random.choice(resolution_notes_samples[status])

        # Create the compliance warning
        ComplianceWarning.objects.create(
            asset=asset,
            detection_date=fake.date_time_between(start_date='-3M', end_date='now'),
            category="SOFTWARE_NO_LICENCIADO",
            description="",  # Can be empty as per requirements
            evidence=evidence,
            status=status,
            resolved_by=resolved_by,
            resolution_notes=resolution_notes
        )

        warnings_created += 1

        if warnings_created % 10 == 0:
            print(f"  - {warnings_created}/{TARGET_WARNINGS} compliance warnings created...")

    print(f"  - {warnings_created}/{TARGET_WARNINGS} compliance warnings created... Completed!")
    return warnings_created


def create_audit_logs(users, assets):
    """Create audit logs simulating past system actions."""

    TARGET_LOGS = 30

    # Available actions
    actions = ["CREATE", "UPDATE", "DELETE"]

    # Target tables and their typical operations
    target_tables = [
        "Asset",
        "Employee",
        "SoftwareCatalog",
        "InstalledSoftware",
        "ComplianceWarning",
    ]

    # Sample details for different actions
    sample_details = {
        "Asset": {
            "CREATE": {"inventory_code": "UPLA-NOTE-0099", "asset_type": "NOTEBOOK", "brand": "Dell"},
            "UPDATE": {"field": "status", "old_value": "IN_STORAGE", "new_value": "ASSIGNED"},
            "DELETE": {"inventory_code": "UPLA-DESK-0050", "reason": "Equipo obsoleto"},
        },
        "Employee": {
            "CREATE": {"rut": "12.345.678-9", "name": "Juan Pérez"},
            "UPDATE": {"field": "department", "old_value": "TI", "new_value": "Finanzas"},
            "DELETE": {"rut": "98.765.432-1", "reason": "Empleado retirado"},
        },
        "SoftwareCatalog": {
            "CREATE": {"name": "Slack", "developer": "Slack Technologies"},
            "UPDATE": {"field": "name", "old_value": "Office 2019", "new_value": "Office 365"},
            "DELETE": {"name": "Software obsoleto", "reason": "Ya no se utiliza"},
        },
        "InstalledSoftware": {
            "CREATE": {"asset": "UPLA-NOTE-0045", "software": "Google Chrome", "version": "120.0.0"},
            "UPDATE": {"field": "version", "old_value": "119.0.0", "new_value": "120.0.0"},
            "DELETE": {"asset": "UPLA-DESK-0022", "software": "WinRAR", "reason": "Licencia vencida"},
        },
        "ComplianceWarning": {
            "CREATE": {"asset": "UPLA-NOTE-0078", "category": "SOFTWARE_NO_LICENCIADO"},
            "UPDATE": {"field": "status", "old_value": "NEW", "new_value": "RESOLVED"},
            "DELETE": {"id": 123, "reason": "Falso positivo confirmado"},
        },
    }

    logs_created = 0

    for _ in range(TARGET_LOGS):
        action = random.choice(actions)
        table = random.choice(target_tables)
        user = random.choice(users)

        # Get sample details for this table and action
        details = sample_details[table][action].copy()

        # Add timestamp variation to details
        details["timestamp"] = fake.date_time_between(start_date='-6M', end_date='now').isoformat()

        # Random target_id
        target_id = random.randint(1, 200)

        AuditLog.objects.create(
            system_user=user,
            action=action,
            target_table=table,
            target_id=target_id,
            details=details,
            timestamp=fake.date_time_between(start_date='-6M', end_date='now')
        )

        logs_created += 1

        if logs_created % 10 == 0:
            print(f"  - {logs_created}/{TARGET_LOGS} audit logs created...")

    print(f"  - {logs_created}/{TARGET_LOGS} audit logs created... Completed!")
    return logs_created
