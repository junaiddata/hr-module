from django.contrib import admin
from .models import Employee, ChangeLog, Leave, Mol, Notification, Role, SalaryStructure, PayrollRun, PayrollEntry, Vehicle

admin.site.register(Employee)
admin.site.register(ChangeLog)
admin.site.register(Mol)
admin.site.register(Role)
admin.site.register(SalaryStructure)
admin.site.register(PayrollRun)
admin.site.register(PayrollEntry)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'ownership', 'car_number', 'car_and_model', 'company', 'mulkiya_expiry']
    list_filter = ['ownership', 'company']
    search_fields = ['name', 'car_number', 'model', 'car_and_model', 'company', 'traffic_code']


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'expected_from', 'expected_to', 'rejoined_on']
    list_filter = ['leave_type', 'expected_from']
    search_fields = ['employee__emp_name', 'reported_to']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'created_at', 'is_read']
    list_filter = ['created_at', 'is_read']
    search_fields = ['title', 'message', 'employee__emp_name']
    ordering = ['-created_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('employee')