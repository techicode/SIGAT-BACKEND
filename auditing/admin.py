# auditing/admin.py
from django.contrib import admin
from .models import AuditLog, AssetCheckin, ComplianceWarning

admin.site.register(AuditLog)
admin.site.register(AssetCheckin)
admin.site.register(ComplianceWarning)