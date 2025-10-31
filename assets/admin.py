# assets/admin.py
from django.contrib import admin
from .models import Asset, ComputerDetail, StorageDevice, GraphicsCard

admin.site.register(Asset)
admin.site.register(ComputerDetail)
admin.site.register(StorageDevice)
admin.site.register(GraphicsCard)