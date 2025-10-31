# software/admin.py
from django.contrib import admin
from .models import SoftwareCatalog, InstalledSoftware, License, Vulnerability

admin.site.register(SoftwareCatalog)
admin.site.register(InstalledSoftware)
admin.site.register(License)
admin.site.register(Vulnerability)