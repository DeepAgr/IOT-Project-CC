from django.contrib import admin
from .models import SensorData
from import_export.admin import ImportExportModelAdmin

@admin.register(SensorData)
class SensorDataAdmin(ImportExportModelAdmin):
    list_display = ('timestamp', 'temperature', 'humidity', 'gas_value',)
