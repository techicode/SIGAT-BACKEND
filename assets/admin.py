# assets/admin.py
from django.contrib import admin
from .models import Asset, ComputerDetail, StorageDevice, GraphicsCard


class StorageDeviceInline(admin.TabularInline):
    model = StorageDevice
    extra = 1


class GraphicsCardInline(admin.TabularInline):
    model = GraphicsCard
    extra = 1


class AssetAdmin(admin.ModelAdmin):

    list_display = ("inventory_code", "asset_type", "status", "employee", "department")

    list_filter = ("status", "asset_type", "department")

    search_fields = (
        "inventory_code",
        "serial_number",
        "employee__first_name",
        "employee__last_name",
        "employee__rut",
    )

    inlines = [StorageDeviceInline, GraphicsCardInline]


admin.site.register(Asset, AssetAdmin)
admin.site.register(ComputerDetail)
admin.site.register(StorageDevice)
admin.site.register(GraphicsCard)
