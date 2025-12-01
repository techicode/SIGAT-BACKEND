"""
Django management command to load realistic demo data for SIGAT MVP presentation.

Usage: python manage.py load_demo_data

This will:
1. DELETE ALL existing data (except migrations)
2. Create realistic demo data from scratch
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import datetime, timedelta
import random

from users.models import CustomUser, Department, Employee
from assets.models import Asset, ComputerDetail, StorageDevice, GraphicsCard
from software.models import SoftwareCatalog, License, InstalledSoftware, Vulnerability
from auditing.models import ComplianceWarning, AuditLog


class Command(BaseCommand):
    help = 'Load realistic demo data for SIGAT MVP presentation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('  ADVERTENCIA: Este comando borrará TODOS los datos existentes'))
        self.stdout.write(self.style.WARNING('='*80 + '\n'))

        confirm = input('¿Estás seguro de que deseas continuar? (escribe "SI" para confirmar): ')
        if confirm != 'SI':
            self.stdout.write(self.style.ERROR('Operación cancelada.'))
            return

        self.stdout.write(self.style.SUCCESS('\nIniciando carga de datos de demostración...\n'))

        with transaction.atomic():
            # Step 1: Delete all data
            self.stdout.write('🗑️  Borrando datos existentes...')
            self.delete_all_data()
            self.stdout.write(self.style.SUCCESS('   ✓ Datos borrados\n'))

            # Step 2: Create departments
            self.stdout.write('🏢 Creando departamentos...')
            departments = self.create_departments()
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(departments)} departamentos creados\n'))

            # Step 3: Create IT staff (admins and technicians)
            self.stdout.write('👥 Creando personal IT...')
            admins, technicians = self.create_it_staff()
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(admins)} admins y {len(technicians)} técnicos creados\n'))

            # Step 4: Create employees
            self.stdout.write('👤 Creando empleados...')
            employees = self.create_employees(departments)
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(employees)} empleados creados\n'))

            # Step 5: Create software catalog
            self.stdout.write('💿 Creando catálogo de software...')
            software_list = self.create_software_catalog()
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(software_list)} software en catálogo\n'))

            # Step 6: Create assets
            self.stdout.write('💻 Creando assets...')
            assets = self.create_assets(employees, departments)
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(assets)} assets creados\n'))

            # Step 7: Install software on assets
            self.stdout.write('📦 Instalando software en assets...')
            installed_count = self.install_software_on_assets(assets, software_list)
            self.stdout.write(self.style.SUCCESS(f'   ✓ {installed_count} instalaciones realizadas\n'))

            # Step 8: Create licenses
            self.stdout.write('🔑 Creando licencias...')
            licenses = self.create_licenses(software_list, assets)
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(licenses)} licencias creadas\n'))

            # Step 9: Create compliance warnings
            self.stdout.write('⚠️  Creando advertencias de cumplimiento...')
            warnings = self.create_compliance_warnings(assets, admins + technicians)
            self.stdout.write(self.style.SUCCESS(f'   ✓ {len(warnings)} advertencias creadas\n'))

            # Step 10: Create audit logs
            self.stdout.write('📋 Creando registros de auditoría...')
            audit_count = self.create_audit_logs(admins + technicians, assets, employees)
            self.stdout.write(self.style.SUCCESS(f'   ✓ {audit_count} registros de auditoría creados\n'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('  ✅ DATOS DE DEMOSTRACIÓN CARGADOS EXITOSAMENTE'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        self.stdout.write('\n📊 Resumen:')
        self.stdout.write(f'   • Departamentos: {len(departments)}')
        self.stdout.write(f'   • Admins: {len(admins)}')
        self.stdout.write(f'   • Técnicos: {len(technicians)}')
        self.stdout.write(f'   • Empleados: {len(employees)}')
        self.stdout.write(f'   • Assets: {len(assets)}')
        self.stdout.write(f'   • Software en catálogo: {len(software_list)}')
        self.stdout.write(f'   • Licencias: {len(licenses)}')
        self.stdout.write(f'   • Advertencias: {len(warnings)}')
        self.stdout.write(f'   • Registros de auditoría: {audit_count}\n')

        self.stdout.write(self.style.SUCCESS('🎉 Sistema listo para demostración MVP!\n'))
        self.stdout.write('📧 Credenciales de acceso:')
        self.stdout.write('   Admin: luis.saez@upla.cl / calama1313')
        self.stdout.write('   Técnico: diego.salazar@upla.cl / calama1313\n')

    def delete_all_data(self):
        """Delete all existing data"""
        AuditLog.objects.all().delete()
        ComplianceWarning.objects.all().delete()
        InstalledSoftware.objects.all().delete()
        License.objects.all().delete()
        Vulnerability.objects.all().delete()
        SoftwareCatalog.objects.all().delete()
        GraphicsCard.objects.all().delete()
        StorageDevice.objects.all().delete()
        ComputerDetail.objects.all().delete()
        Asset.objects.all().delete()
        Employee.objects.all().delete()
        CustomUser.objects.all().delete()
        Department.objects.all().delete()

    def create_departments(self):
        """Create UPLA departments"""
        dept_names = [
            "Departamento de Ciencia de Datos e Informática",
            "Departamento de Ciencias de la Ingeniería para la Sostenibilidad",
            "Departamento de Ingeniería Industrial y Gestión Organizacional",
            "Departamento de Salud, Comunidad y Gestión",
            "Departamento de Rehabilitación, Intervención y Abordaje Terapéutico",
            "Departamento de Filosofía, Historia y Turismo",
            "Departamento de Literatura y Lingüística",
            "Departamento de Lenguas Extranjeras",
            "Departamento de Estudios Territoriales y Diálogos Interdisciplinarios",
            "Departamento de Género, Política y Cultura",
            "Departamento de Mediaciones y Subjetividades",
            "Departamento de Matemática, Física y Computación",
            "Departamento de Ciencias y Geografía",
            "Departamento de Educación Artística",
            "Departamento de Artes Integradas",
            "Departamento de Ciencias de la Actividad Física",
            "Departamento de Ciencias del Deporte",
            "Departamento de Ciencias de la Educación",
        ]

        departments = []
        for name in dept_names:
            dept = Department.objects.create(name=name)
            departments.append(dept)

        return departments

    def create_it_staff(self):
        """Create IT staff (admins and technicians)"""
        password = make_password('calama1313')

        # Admins
        admins = [
            CustomUser.objects.create(
                username='luis.saez',
                email='luis.saez@upla.cl',
                first_name='Luis',
                last_name='Sáez',
                role='ADMIN',
                is_staff=True,
                is_superuser=True,
                password=password
            ),
            CustomUser.objects.create(
                username='maria.gonzalez',
                email='maria.gonzalez@upla.cl',
                first_name='María',
                last_name='González',
                role='ADMIN',
                is_staff=True,
                is_superuser=True,
                password=password
            ),
        ]

        # Technicians
        tech_data = [
            ('diego.salazar', 'Diego', 'Salazar'),
            ('ana.martinez', 'Ana', 'Martínez'),
            ('carlos.rojas', 'Carlos', 'Rojas'),
            ('patricia.silva', 'Patricia', 'Silva'),
            ('jorge.mora', 'Jorge', 'Mora'),
            ('claudia.vega', 'Claudia', 'Vega'),
        ]

        technicians = []
        for username, first, last in tech_data:
            tech = CustomUser.objects.create(
                username=username,
                email=f'{username}@upla.cl',
                first_name=first,
                last_name=last,
                role='TECHNICIAN',
                is_staff=True,
                password=password
            )
            technicians.append(tech)

        return admins, technicians

    def create_employees(self, departments):
        """Create employees distributed across departments"""
        # Chilean names for realism
        first_names = [
            'Roberto', 'Carmen', 'Francisco', 'Isabel', 'Andrés', 'Gabriela', 'Ricardo', 'Lorena',
            'Felipe', 'Valentina', 'Sebastián', 'Camila', 'Alejandro', 'Daniela', 'Rodrigo', 'Fernanda',
            'Manuel', 'Carolina', 'Pablo', 'Andrea', 'Cristian', 'Mónica', 'Diego', 'Paola',
            'Gonzalo', 'Marcela', 'Mauricio', 'Soledad', 'Claudio', 'Verónica', 'Raúl', 'Claudia',
            'Sergio', 'Beatriz', 'Eduardo', 'Rosa', 'Héctor', 'Silvia', 'Jaime', 'Teresa',
            'Fernando', 'Gloria', 'Víctor', 'Pilar', 'Miguel', 'Cecilia', 'Alberto', 'Ángela',
            'Luis', 'Natalia', 'Pedro', 'Carla', 'Mario', 'Lucía', 'Jorge', 'Mariana',
            'Ignacio', 'Javiera', 'Tomás', 'Francisca', 'Matías', 'Constanza', 'Nicolás', 'Catalina',
        ]

        last_names = [
            'González', 'Muñoz', 'Rojas', 'Díaz', 'Pérez', 'Soto', 'Contreras', 'Silva',
            'Martínez', 'Sepúlveda', 'Morales', 'Rodríguez', 'López', 'Fuentes', 'Hernández', 'Torres',
            'Araya', 'Flores', 'Espinoza', 'Valenzuela', 'Castillo', 'Núñez', 'Tapia', 'Reyes',
            'Vásquez', 'Ramírez', 'Campos', 'Cortés', 'Medina', 'Figueroa', 'Gutiérrez', 'Alarcón',
        ]

        employees = []
        # Create 160-170 employees (10-20 more than assets)
        num_employees = random.randint(160, 170)

        # Cargos por tipo de departamento (departamentos académicos UPLA)
        positions_by_dept = {
            'Departamento de Artes Integradas': ['Director de Departamento', 'Profesor Titular', 'Profesor Asociado', 'Profesor Asistente', 'Ayudante', 'Secretaria Académica'],
            'Departamento de Ciencia de Datos e Informática': ['Director de Departamento', 'Profesor Titular', 'Ingeniero en Informática', 'Data Scientist', 'Analista de Datos', 'Asistente de Investigación'],
            'Departamento de Ciencias de la Actividad Física': ['Director de Departamento', 'Profesor de Educación Física', 'Kinesiólogo', 'Preparador Físico', 'Coordinador Deportivo', 'Secretaria'],
            'Departamento de Ciencias de la Educación': ['Director de Departamento', 'Profesor Titular', 'Investigador Educacional', 'Psicopedagogo', 'Coordinador Pedagógico', 'Secretaria Académica'],
            'Departamento de Ciencias de la Ingeniería para la Sostenibilidad': ['Director de Departamento', 'Ingeniero Civil', 'Profesor Asociado', 'Investigador', 'Técnico de Laboratorio', 'Asistente'],
            'Departamento de Ciencias del Deporte': ['Director de Departamento', 'Profesor de Deportes', 'Entrenador', 'Kinesiólogo Deportivo', 'Coordinador', 'Administrativo'],
            'Departamento de Ciencias y Geografía': ['Director de Departamento', 'Profesor Titular', 'Geógrafo', 'Investigador', 'Técnico GIS', 'Secretaria'],
            'Departamento de Educación Artística': ['Director de Departamento', 'Profesor de Arte', 'Artista Docente', 'Coordinador de Talleres', 'Asistente', 'Administrativo'],
            'Departamento de Estudios Territoriales y Diálogos Interdisciplinarios': ['Director de Departamento', 'Investigador', 'Profesor Asociado', 'Analista Territorial', 'Coordinador de Proyectos', 'Asistente de Investigación'],
            'Departamento de Filosofía, Historia y Turismo': ['Director de Departamento', 'Profesor Titular', 'Historiador', 'Filósofo', 'Gestor Turístico', 'Secretaria Académica'],
            'Departamento de Género, Política y Cultura': ['Director de Departamento', 'Investigador', 'Profesor Asociado', 'Analista de Políticas Públicas', 'Coordinador', 'Asistente'],
            'Departamento de Ingeniería Industrial y Gestión Organizacional': ['Director de Departamento', 'Ingeniero Industrial', 'Profesor Titular', 'Analista de Procesos', 'Consultor', 'Secretaria'],
            'Departamento de Lenguas Extranjeras': ['Director de Departamento', 'Profesor de Inglés', 'Profesor de Francés', 'Traductor', 'Coordinador Idiomas', 'Secretaria Académica'],
            'Departamento de Literatura y Lingüística': ['Director de Departamento', 'Profesor Titular', 'Lingüista', 'Investigador Literario', 'Editor', 'Secretaria'],
            'Departamento de Matemática, Física y Computación': ['Director de Departamento', 'Profesor Titular', 'Matemático', 'Físico', 'Ingeniero en Computación', 'Técnico de Laboratorio'],
            'Departamento de Mediaciones y Subjetividades': ['Director de Departamento', 'Psicólogo', 'Investigador', 'Profesor Asociado', 'Coordinador', 'Asistente'],
            'Departamento de Rehabilitación, Intervención y Abordaje Terapéutico': ['Director de Departamento', 'Kinesiólogo', 'Terapeuta Ocupacional', 'Fonoaudiólogo', 'Coordinador Clínico', 'Secretaria'],
            'Departamento de Salud, Comunidad y Gestión': ['Director de Departamento', 'Enfermero', 'Trabajador Social', 'Gestor en Salud', 'Coordinador Comunitario', 'Administrativo'],
        }

        for i in range(num_employees):
            first_name = random.choice(first_names)
            last_name1 = random.choice(last_names)
            last_name2 = random.choice(last_names)
            last_name = f"{last_name1} {last_name2}"

            # Generate realistic Chilean RUT
            rut_number = random.randint(10000000, 25000000)
            rut_dv = self.calculate_rut_dv(rut_number)
            rut = f"{rut_number}-{rut_dv}"

            # Email
            username = f"{first_name.lower()}.{last_name1.lower()}{i}"
            email = f"{username}@upla.cl"

            # Assign to department
            department = random.choice(departments)

            # Assign position based on department
            dept_positions = positions_by_dept.get(department.name, ['Administrativo', 'Asistente', 'Coordinador', 'Analista'])
            position = random.choice(dept_positions)

            emp = Employee.objects.create(
                rut=rut,
                first_name=first_name,
                last_name=last_name,
                email=email,
                position=position,
                department=department
            )
            employees.append(emp)

        return employees

    def calculate_rut_dv(self, rut):
        """Calculate Chilean RUT verification digit"""
        reversed_digits = map(int, reversed(str(rut)))
        factors = [2, 3, 4, 5, 6, 7]
        s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
        dv = 11 - (s % 11)
        if dv == 11:
            return '0'
        elif dv == 10:
            return 'K'
        else:
            return str(dv)

    def create_software_catalog(self):
        """Create realistic software catalog"""
        software_data = [
            # Microsoft
            ('Microsoft Office', 'Microsoft'),
            ('Microsoft Teams', 'Microsoft'),
            ('Microsoft Edge', 'Microsoft'),

            # Adobe
            ('Adobe Acrobat Reader', 'Adobe'),
            ('Adobe Photoshop', 'Adobe'),
            ('Adobe Illustrator', 'Adobe'),

            # Browsers
            ('Google Chrome', 'Google'),
            ('Mozilla Firefox', 'Mozilla'),

            # Communication
            ('Zoom', 'Zoom Video Communications'),
            ('Slack', 'Slack Technologies'),

            # Development
            ('Visual Studio Code', 'Microsoft'),
            ('Git', 'Git SCM'),
            ('Python', 'Python Software Foundation'),

            # Utilities
            ('WinRAR', 'RARLAB'),
            ('7-Zip', '7-Zip'),
            ('VLC Media Player', 'VideoLAN'),

            # Productivity
            ('Notion', 'Notion Labs'),
            ('Evernote', 'Evernote Corporation'),

            # Security
            ('Malwarebytes', 'Malwarebytes'),

            # Data Analysis
            ('Tableau Desktop', 'Tableau'),
            ('SPSS Statistics', 'IBM'),

            # Educational
            ('MATLAB', 'MathWorks'),
            ('Mathematica', 'Wolfram'),

            # Graphics
            ('AutoCAD', 'Autodesk'),
            ('SketchUp', 'Trimble'),

            # Other
            ('TeamViewer', 'TeamViewer'),
            ('Dropbox', 'Dropbox'),
            ('Spotify', 'Spotify AB'),
            ('Discord', 'Discord Inc'),
            ('WhatsApp Desktop', 'WhatsApp'),
        ]

        software_list = []
        for name, developer in software_data:
            sw = SoftwareCatalog.objects.create(
                name=name,
                developer=developer
            )
            software_list.append(sw)

        return software_list

    def create_assets(self, employees, departments):
        """Create realistic assets (140-150)"""
        num_assets = random.randint(140, 150)

        # Asset data
        notebook_brands = ['Dell', 'HP', 'Lenovo', 'ASUS', 'Acer']
        notebook_models = {
            'Dell': ['Latitude 5420', 'Latitude 7420', 'Inspiron 15 3000', 'Vostro 3510'],
            'HP': ['EliteBook 840 G8', 'ProBook 450 G8', 'Pavilion 15', 'ZBook 15 G8'],
            'Lenovo': ['ThinkPad T14', 'ThinkPad X1 Carbon', 'IdeaPad 3', 'ThinkBook 15'],
            'ASUS': ['VivoBook 15', 'ZenBook 14', 'TUF Gaming F15', 'ExpertBook B9'],
            'Acer': ['Aspire 5', 'Swift 3', 'TravelMate P2', 'Nitro 5'],
        }

        desktop_brands = ['Dell', 'HP', 'Lenovo']
        desktop_models = {
            'Dell': ['OptiPlex 7090', 'OptiPlex 3090', 'Precision 3660'],
            'HP': ['EliteDesk 800 G8', 'ProDesk 400 G7', 'Z2 Tower G9'],
            'Lenovo': ['ThinkCentre M90t', 'ThinkCentre M720q', 'ThinkStation P340'],
        }

        cpu_models = [
            'Intel Core i3-10100', 'Intel Core i5-10400', 'Intel Core i5-11400',
            'Intel Core i7-10700', 'Intel Core i7-11700', 'AMD Ryzen 5 5600G',
            'AMD Ryzen 7 5700G', 'Intel Core i3-1115G4', 'Intel Core i5-1135G7',
            'Intel Core i7-1165G7', 'Intel Core i7-1185G7'
        ]

        motherboard_brands = ['Dell', 'HP', 'Lenovo', 'ASUS', 'Gigabyte', 'MSI']

        gpu_models = [
            'Intel UHD Graphics 630', 'Intel Iris Xe Graphics', 'NVIDIA GeForce MX450',
            'NVIDIA GeForce GTX 1650', 'AMD Radeon Graphics', 'Intel UHD Graphics 730'
        ]

        storage_brands = ['Samsung', 'Western Digital', 'Kingston', 'Crucial', 'Seagate']
        storage_models = {
            'Samsung': ['970 EVO Plus', '980 PRO', '870 EVO', '860 EVO'],
            'Western Digital': ['Blue SN570', 'Black SN850', 'Blue SA510'],
            'Kingston': ['A2000', 'NV2', 'KC3000'],
            'Crucial': ['P3', 'P5 Plus', 'MX500'],
            'Seagate': ['BarraCuda', 'FireCuda 530', 'IronWolf'],
        }

        os_versions = {
            'Windows 10': ['10.0.19044', '10.0.19045'],  # 80%
            'Windows 11': ['10.0.22621', '10.0.22631'],  # 20%
        }

        # RAM distribution
        ram_distribution = [4] * 5 + [8] * 60 + [16] * 30 + [32] * 5  # 100 items total

        assets = []
        # 80% notebooks, 20% desktops
        num_notebooks = int(num_assets * 0.8)
        num_desktops = num_assets - num_notebooks

        # 80% assigned, 20% distributed among other statuses
        num_assigned = int(num_assets * 0.8)
        employees_for_assignment = random.sample(employees, num_assigned)

        # Some employees will have 2 assets
        num_double_assigned = random.randint(5, 10)
        double_assigned_employees = random.sample(employees_for_assignment[:num_double_assigned], num_double_assigned)
        employees_for_assignment.extend(double_assigned_employees)
        random.shuffle(employees_for_assignment)

        for i in range(num_assets):
            # Determine type
            if i < num_notebooks:
                asset_type = 'NOTEBOOK'
                brand = random.choice(notebook_brands)
                model = random.choice(notebook_models[brand])
            else:
                asset_type = 'DESKTOP'
                brand = random.choice(desktop_brands)
                model = random.choice(desktop_models[brand])

            # Inventory code
            inventory_code = f"UPLA-{asset_type[:2]}-{str(i+1).zfill(4)}"

            # Status and assignment
            if i < num_assigned:
                status = 'ASIGNADO'
                employee = employees_for_assignment[i]
                department = employee.department
            else:
                status = random.choice(['EN_BODEGA', 'DE_BAJA', 'EN_REPARACION'])
                employee = None
                department = random.choice(departments)

            # Acquisition date (last 2-5 years)
            days_ago = random.randint(365*2, 365*5)
            acquisition_date = timezone.now().date() - timedelta(days=days_ago)

            # Create asset
            asset = Asset.objects.create(
                inventory_code=inventory_code,
                asset_type=asset_type,
                brand=brand,
                model=model,
                serial_number=f"SN{random.randint(100000000, 999999999)}",
                acquisition_date=acquisition_date,
                status=status,
                employee=employee,
                department=department
            )

            # Create computer details
            # OS distribution
            if random.random() < 0.8:  # 80% Windows 10
                os_name = 'Windows 10 Pro'
                os_version = random.choice(os_versions['Windows 10'])
            else:  # 20% Windows 11
                os_name = 'Windows 11 Pro'
                os_version = random.choice(os_versions['Windows 11'])

            # RAM distribution
            ram_gb = random.choice(ram_distribution)

            # CPU
            cpu_model = random.choice(cpu_models)

            # Motherboard
            mb_brand = random.choice(motherboard_brands)
            mb_model = f"{mb_brand}-MB-{random.randint(1000, 9999)}"

            # Unique identifier (BIOS UUID)
            unique_id = f"{random.randint(10000000, 99999999):08x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(100000000000, 999999999999):012x}"

            computer_detail = ComputerDetail.objects.create(
                asset=asset,
                os_name=os_name,
                os_version=os_version,
                os_arch='64-bit',
                cpu_model=cpu_model,
                ram_gb=ram_gb,
                motherboard_manufacturer=mb_brand,
                motherboard_model=mb_model,
                unique_identifier=unique_id
            )

            # Storage devices (1-2 drives)
            num_drives = random.choice([1, 1, 1, 2])  # Mostly 1, sometimes 2
            for d in range(num_drives):
                storage_brand = random.choice(storage_brands)
                storage_model = random.choice(storage_models[storage_brand])

                if d == 0:  # Main drive (SSD)
                    capacity_gb = random.choice([256, 512, 512, 1024])
                    free_gb = capacity_gb * random.uniform(0.2, 0.7)
                else:  # Secondary drive (HDD)
                    capacity_gb = random.choice([1024, 2048])
                    free_gb = capacity_gb * random.uniform(0.3, 0.8)

                StorageDevice.objects.create(
                    asset=asset,
                    model=f"{storage_brand} {storage_model}",
                    serial_number=f"DSK{random.randint(100000000, 999999999)}",
                    capacity_gb=capacity_gb,
                    free_space_gb=round(free_gb, 2)
                )

            # Graphics card
            gpu_model = random.choice(gpu_models)
            GraphicsCard.objects.create(
                asset=asset,
                model_name=gpu_model
            )

            assets.append(asset)

        return assets

    def install_software_on_assets(self, assets, software_list):
        """Install ~15 software on each asset with realistic versions and dates"""
        installed_count = 0

        # Versiones realistas para cada software (con algunas variaciones)
        software_versions = {
            'Microsoft Office': ['16.0.15831', '16.0.16130', '16.0.16327', '16.0.16501'],
            'Adobe Photoshop': ['24.6.0', '24.7.0', '25.0.0', '25.1.0'],
            'Adobe Illustrator': ['27.8.0', '27.9.0', '28.0.0', '28.1.0'],
            'Adobe Acrobat Reader': ['23.003.20244', '23.006.20360', '24.001.20604'],
            'AutoCAD': ['2023.1.0', '2024.0.0', '2024.1.0'],
            'Google Chrome': ['119.0.6045.105', '120.0.6099.109', '121.0.6167.85'],
            'Mozilla Firefox': ['120.0.1', '121.0', '122.0'],
            'Microsoft Edge': ['119.0.2151.97', '120.0.2210.89', '121.0.2277.83'],
            'Visual Studio Code': ['1.84.2', '1.85.1', '1.86.0'],
            'Python': ['3.10.11', '3.11.5', '3.11.7', '3.12.0'],
            'Git': ['2.42.0', '2.43.0', '2.44.0'],
            'WinRAR': ['6.23', '6.24', '7.00'],
            '7-Zip': ['23.01', '24.03', '24.06'],
            'VLC Media Player': ['3.0.18', '3.0.19', '3.0.20'],
            'Zoom': ['5.16.5', '5.17.0', '5.17.5'],
            'Microsoft Teams': ['1.6.00.30866', '1.6.00.32462', '1.7.00.1234'],
            'Slack': ['4.35.126', '4.36.134', '4.37.98'],
            'Discord': ['1.0.9024', '1.0.9025', '1.0.9027'],
            'Spotify': ['1.2.25.1011', '1.2.26.1187', '1.2.28.582'],
            'WhatsApp Desktop': ['2.2348.10', '2.2349.12', '2.2350.8'],
            'Dropbox': ['184.4.6345', '186.4.6478', '188.4.6589'],
            'MATLAB': ['R2023a', 'R2023b', 'R2024a'],
            'Mathematica': ['13.3.0', '13.3.1', '14.0.0'],
            'SPSS Statistics': ['28.0.1.0', '29.0.0.0', '29.0.1.0'],
            'Tableau Desktop': ['2023.2.3', '2023.3.1', '2024.1.0'],
            'SketchUp': ['23.0.419', '23.1.329', '24.0.484'],
            'TeamViewer': ['15.48.4', '15.49.5', '15.50.5'],
            'Notion': ['2.2.1', '2.3.0', '2.3.3'],
            'Evernote': ['10.68.2', '10.69.1', '10.70.3'],
            'Malwarebytes': ['4.6.3.241', '4.6.4.248', '4.6.5.256'],
        }

        # Rango de fechas de instalación (últimos 12 meses)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)

        for asset in assets:
            # Each asset gets 12-18 software installed
            num_software = random.randint(12, 18)
            selected_software = random.sample(software_list, num_software)

            for software in selected_software:
                # Get realistic version
                versions = software_versions.get(software.name, ['1.0.0', '1.1.0', '1.2.0', '2.0.0'])
                version = random.choice(versions)

                # Random installation date within last year
                days_ago = random.randint(30, 365)
                install_date = end_date - timedelta(days=days_ago)

                InstalledSoftware.objects.create(
                    asset=asset,
                    software=software,
                    version=version,
                    install_date=install_date
                )
                installed_count += 1

        return installed_count

    def create_licenses(self, software_list, assets):
        """Create realistic license packs"""
        licenses = []

        # Find software in catalog
        office_sw = next((sw for sw in software_list if 'Office' in sw.name), None)
        adobe_sw = next((sw for sw in software_list if 'Photoshop' in sw.name or 'Illustrator' in sw.name), None)
        winrar_sw = next((sw for sw in software_list if 'WinRAR' in sw.name), None)

        # Office 365 - Pack 1 (20 licenses)
        if office_sw:
            office_assets_pool = [a for a in assets if a.employee and
                           InstalledSoftware.objects.filter(asset=a, software=office_sw).exists()]
            for i in range(20):
                key = f"XXXXX-XXXXX-XXXXX-{random.randint(10000, 99999)}"
                expiry = timezone.now().date() + timedelta(days=365)

                lic = License.objects.create(
                    software=office_sw,
                    license_key=key,
                    expiration_date=expiry,
                    quantity=1
                )
                licenses.append(lic)

                # Assign license to an InstalledSoftware record
                if office_assets_pool and random.random() < 0.9:  # 90% assigned
                    asset = random.choice(office_assets_pool)
                    office_assets_pool.remove(asset)

                    # Update the InstalledSoftware record
                    installed = InstalledSoftware.objects.filter(asset=asset, software=office_sw).first()
                    if installed:
                        installed.license = lic
                        installed.save()

        # Office 365 - Pack 2 (20 licenses)
        if office_sw:
            # Get assets with Office but no license yet
            office_assets_pool2 = [a for a in assets if a.employee and
                           InstalledSoftware.objects.filter(asset=a, software=office_sw, license__isnull=True).exists()]
            for i in range(20):
                key = f"YYYYY-YYYYY-YYYYY-{random.randint(10000, 99999)}"
                expiry = timezone.now().date() + timedelta(days=730)

                lic = License.objects.create(
                    software=office_sw,
                    license_key=key,
                    expiration_date=expiry,
                    quantity=1
                )
                licenses.append(lic)

                # Assign license to an InstalledSoftware record without license
                if office_assets_pool2 and random.random() < 0.9:
                    asset = random.choice(office_assets_pool2)
                    office_assets_pool2.remove(asset)

                    # Update the InstalledSoftware record
                    installed = InstalledSoftware.objects.filter(asset=asset, software=office_sw, license__isnull=True).first()
                    if installed:
                        installed.license = lic
                        installed.save()

        # Adobe Suite (5 licenses)
        if adobe_sw:
            adobe_assets_pool = [a for a in assets if a.employee and
                          InstalledSoftware.objects.filter(asset=a, software=adobe_sw).exists()]
            for i in range(5):
                key = f"ADOBE-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
                expiry = timezone.now().date() + timedelta(days=365)

                lic = License.objects.create(
                    software=adobe_sw,
                    license_key=key,
                    expiration_date=expiry,
                    quantity=1
                )
                licenses.append(lic)

                # Assign license to an InstalledSoftware record
                if adobe_assets_pool:
                    asset = random.choice(adobe_assets_pool)
                    adobe_assets_pool.remove(asset)

                    # Update the InstalledSoftware record
                    installed = InstalledSoftware.objects.filter(asset=asset, software=adobe_sw).first()
                    if installed:
                        installed.license = lic
                        installed.save()

        # WinRAR (50 licenses)
        if winrar_sw:
            winrar_assets_pool = [a for a in assets if a.employee and
                           InstalledSoftware.objects.filter(asset=a, software=winrar_sw).exists()]
            for i in range(50):
                key = f"WINRAR-{random.randint(100000, 999999)}"
                # WinRAR licenses don't usually expire, but let's set far future
                expiry = timezone.now().date() + timedelta(days=3650)

                lic = License.objects.create(
                    software=winrar_sw,
                    license_key=key,
                    expiration_date=expiry,
                    quantity=1
                )
                licenses.append(lic)

                # Assign license to an InstalledSoftware record
                if winrar_assets_pool and random.random() < 0.7:  # 70% assigned
                    asset = random.choice(winrar_assets_pool)
                    winrar_assets_pool.remove(asset)

                    # Update the InstalledSoftware record
                    installed = InstalledSoftware.objects.filter(asset=asset, software=winrar_sw).first()
                    if installed:
                        installed.license = lic
                        installed.save()

        return licenses

    def create_compliance_warnings(self, assets, it_staff):
        """Create SOFTWARE_NO_LICENCIADO warnings from Oct 10 to Nov 30"""
        warnings = []

        # Date range: Oct 10, 2025 to Nov 30, 2025
        start_date = datetime(2025, 10, 10, tzinfo=timezone.get_current_timezone())
        end_date = datetime(2025, 11, 30, tzinfo=timezone.get_current_timezone())
        current_date = start_date

        # Get assets with installed software
        assets_with_software = [a for a in assets if
                               InstalledSoftware.objects.filter(asset=a).exists()]

        # Rutas sospechosas de software pirata/cracks
        suspicious_patterns = [
            # Cracks genéricos
            ('C:\\Users\\{user}\\Downloads\\Adobe_Photoshop_2024_Crack.exe', 'Adobe Photoshop', 'Adobe'),
            ('C:\\Users\\{user}\\Desktop\\Crack\\WinRAR_Universal_Patch.exe', 'WinRAR', 'RARLab'),
            ('C:\\Users\\{user}\\Downloads\\Office365_Activator_2024.exe', 'Microsoft Office 365', 'Microsoft'),
            ('C:\\Temp\\crack_office_2024\\KMSAuto.exe', 'Microsoft Office 365', 'Microsoft'),
            ('C:\\Users\\{user}\\AppData\\Local\\Temp\\keygen_autocad.exe', 'AutoCAD', 'Autodesk'),

            # Software pirata descargado
            ('C:\\Users\\{user}\\Downloads\\Photoshop_2024_Full_Crack\\setup.exe', 'Adobe Photoshop', 'Adobe'),
            ('C:\\Users\\{user}\\Downloads\\Office_Professional_Plus_2024_Crack.iso', 'Microsoft Office', 'Microsoft'),
            ('C:\\Software\\Adobe_CC_2024_Crack\\patch.exe', 'Adobe Creative Cloud', 'Adobe'),
            ('C:\\Descargas\\AutoCAD_2024_Full_Español_Crack.exe', 'AutoCAD', 'Autodesk'),

            # Keygens
            ('C:\\Users\\{user}\\Desktop\\keygen.exe', 'WinRAR', 'RARLab'),
            ('C:\\Windows\\Temp\\KMSpico_v11.exe', 'Microsoft Office 365', 'Microsoft'),
            ('D:\\Software\\Cracks\\Adobe\\keygen_universal.exe', 'Adobe Illustrator', 'Adobe'),
            ('C:\\Program Files\\Common Files\\keygen_office.exe', 'Microsoft Office', 'Microsoft'),

            # Patches sospechosos
            ('C:\\Users\\{user}\\Downloads\\patch_windows.exe', 'Windows', 'Microsoft'),
            ('C:\\Temp\\universal_adobe_patcher_2024.exe', 'Adobe Acrobat', 'Adobe'),
            ('C:\\Users\\{user}\\Desktop\\activador_office.cmd', 'Microsoft Office 365', 'Microsoft'),

            # Torrents
            ('C:\\Users\\{user}\\Downloads\\Torrents\\Office_2024_Pro_Plus_x64.iso', 'Microsoft Office', 'Microsoft'),
            ('C:\\Downloads\\Adobe_Master_Collection_2024_Crack.rar', 'Adobe Master Collection', 'Adobe'),
            ('D:\\Torrents\\AutoCAD_2024_Full_Version\\setup.exe', 'AutoCAD', 'Autodesk'),

            # Software sospechoso en Program Files
            ('C:\\Program Files\\Microsoft Office\\crack\\activator.exe', 'Microsoft Office 365', 'Microsoft'),
            ('C:\\Program Files\\Adobe\\Adobe Photoshop 2024\\amtlib.dll', 'Adobe Photoshop', 'Adobe'),
            ('C:\\Program Files (x86)\\WinRAR\\rarreg.key.txt', 'WinRAR', 'RARLab'),

            # Otros archivos sospechosos
            ('C:\\Users\\{user}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\kms_activator.vbs', 'Microsoft Office', 'Microsoft'),
            ('C:\\ProgramData\\Adobe\\crack_tools\\amtemu.exe', 'Adobe Creative Cloud', 'Adobe'),
            ('C:\\Windows\\System32\\drivers\\etc\\crack_loader.sys', 'Varios', 'Desconocido'),
        ]

        # Comentarios realistas para falsos positivos
        false_positive_comments = [
            'Error del sistema - archivo es parte de instalación legítima con licencia corporativa',
            'Falsa alarma - el nombre del archivo coincide con patrón sospechoso pero es software legal',
            'No es crack - archivo de configuración legítimo con nombre similar a herramienta pirata',
            'Software open source con nombre que activa alerta por error',
            'Alcance de nombre - herramienta de desarrollo legítima detectada incorrectamente',
            'Script de automatización interno que genera falso positivo',
            'Archivo de backup antiguo de instalación legal, no es piratería',
            'Coincidencia de hash con base de datos desactualizada - software es original',
            'Herramienta de diagnóstico autorizada que activa alerta por similitud de nombre',
            'Error de detección - es versión trial legítima descargada del sitio oficial',
        ]

        # Comentarios para warnings resueltas
        resolved_comments = [
            'Software eliminado del equipo. Usuario sancionado según reglamento interno',
            'Licencia adquirida y asignada correctamente. Software ahora en regla',
            'Usuario regularizó situación mediante compra de licencia corporativa',
            'Software desinstalado. Se instaló alternativa open source',
            'Crack eliminado. Software reinstalado con licencia institucional',
            'Archivo sospechoso eliminado. Equipo escaneado y limpiado',
            'Licencia validada en servidor de licencias corporativo',
            'Software pirata removido. Usuario capacitado sobre políticas de uso',
            'Situación regularizada - se asignó licencia del pool corporativo',
            'Equipo formateado y reinstalado con imagen corporativa limpia',
        ]

        usernames = ['jperez', 'mrodriguez', 'cgarcia', 'alopez', 'rmartinez', 'fsanchez',
                    'pgonzalez', 'lhernandez', 'ddiaz', 'vramirez', 'jmunoz', 'mtorres']

        while current_date <= end_date:
            # Create 1-5 warnings per day
            num_warnings_today = random.randint(1, 5)

            for _ in range(num_warnings_today):
                # Pick random asset
                asset = random.choice(assets_with_software)

                # Pick random suspicious pattern
                file_path, software_name, developer = random.choice(suspicious_patterns)
                username = random.choice(usernames)
                file_path = file_path.replace('{user}', username)

                # Random time during business hours (8 AM - 6 PM)
                random_hour = random.randint(8, 18)
                random_minute = random.randint(0, 59)
                random_second = random.randint(0, 59)
                detection_datetime = current_date.replace(hour=random_hour, minute=random_minute, second=random_second)

                # Determine status based on how old the warning is
                days_since = (end_date - current_date).days

                if days_since < 5:  # Last 5 days
                    status = random.choice(['NUEVA', 'NUEVA', 'EN_REVISION'])
                elif days_since < 15:  # 15 days ago
                    status = random.choice(['NUEVA', 'EN_REVISION', 'EN_REVISION', 'RESUELTA'])
                else:  # Older
                    status = random.choice(['RESUELTA', 'RESUELTA', 'FALSO_POSITIVO'])

                # Resolved by and notes
                resolved_by = None
                resolution_notes = ''
                if status in ['EN_REVISION', 'RESUELTA', 'FALSO_POSITIVO']:
                    resolved_by = random.choice(it_staff)
                    if status == 'RESUELTA':
                        resolution_notes = random.choice(resolved_comments)
                    elif status == 'FALSO_POSITIVO':
                        resolution_notes = random.choice(false_positive_comments)

                # Descripción más detallada
                description = f'Detección de archivo sospechoso: {file_path}'
                if 'crack' in file_path.lower() or 'keygen' in file_path.lower() or 'patch' in file_path.lower():
                    description += ' - Posible software pirata o herramienta de activación ilegal'

                warning = ComplianceWarning.objects.create(
                    asset=asset,
                    detection_date=detection_datetime,
                    category='SOFTWARE_NO_LICENCIADO',
                    description=description,
                    evidence={
                        'file_path': file_path,
                        'software': software_name,
                        'developer': developer,
                        'detection_type': 'file_scan',
                        'risk_level': 'HIGH' if 'crack' in file_path.lower() or 'keygen' in file_path.lower() else 'MEDIUM'
                    },
                    status=status,
                    resolved_by=resolved_by,
                    resolution_notes=resolution_notes
                )
                warnings.append(warning)

            # Move to next day
            current_date += timedelta(days=1)

        return warnings

    def create_audit_logs(self, it_staff, assets, employees):
        """Create audit logs from Oct 10 to Nov 30"""
        start_date = datetime(2025, 10, 10, tzinfo=timezone.get_current_timezone())
        end_date = datetime(2025, 11, 30, tzinfo=timezone.get_current_timezone())
        current_date = start_date

        actions = ['CREATE', 'UPDATE', 'DELETE']
        tables = [
            'assets_asset', 'users_employee', 'software_softwarecatalog',
            'software_license', 'auditing_compliancewarning'
        ]

        audit_count = 0

        while current_date <= end_date:
            # Create 5-15 audit logs per day
            num_logs_today = random.randint(5, 15)

            for _ in range(num_logs_today):
                user = random.choice(it_staff)
                action = random.choice(actions)
                table = random.choice(tables)
                target_id = random.randint(1, 100)

                # Random time during the day
                hour = random.randint(8, 18)
                minute = random.randint(0, 59)
                timestamp = current_date.replace(hour=hour, minute=minute)

                details = {
                    'action': action,
                    'table': table,
                    'user': user.username
                }

                AuditLog.objects.create(
                    timestamp=timestamp,
                    system_user=user,
                    action=action,
                    target_table=table,
                    target_id=target_id,
                    details=details
                )
                audit_count += 1

            current_date += timedelta(days=1)

        return audit_count
