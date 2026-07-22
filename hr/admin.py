from django.contrib import admin
from .models import Employee, ChangeLog, Leave, Mol, Notification, Role, SalaryStructure, PayrollRun, PayrollEntry, Vehicle, VehicleService, ManagementMember, TravelRecord, CountryVisa, CompanyProperty, PropertyCategory, Memo, MemoType

admin.site.register(Employee)
admin.site.register(ChangeLog)
admin.site.register(Mol)
admin.site.register(Role)
admin.site.register(SalaryStructure)
admin.site.register(PayrollRun)
admin.site.register(PayrollEntry)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'ownership', 'car_number', 'car_and_model', 'company', 'mulkiya_expiry', 'is_sold']
    list_filter = ['ownership', 'company', 'is_sold']
    search_fields = ['name', 'car_number', 'model', 'car_and_model', 'company', 'traffic_code']


@admin.register(VehicleService)
class VehicleServiceAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'service_type', 'status', 'service_date', 'requested_by', 'cost']
    list_filter = ['status', 'service_type', 'service_date']
    search_fields = ['vehicle__name', 'vehicle__car_number', 'requested_by__emp_name', 'other_detail']
    ordering = ['-service_date', '-created_at']


@admin.register(ManagementMember)
class ManagementMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'relation', 'designation', 'head', 'nationality', 'visa_type']
    list_filter = ['relation', 'visa_type']
    search_fields = ['name', 'designation', 'nationality', 'passport_number', 'eid_number']


@admin.register(TravelRecord)
class TravelRecordAdmin(admin.ModelAdmin):
    list_display = ['member', 'destination', 'departure_date', 'return_date']
    list_filter = ['departure_date']
    search_fields = ['member__name', 'destination', 'purpose']


@admin.register(CountryVisa)
class CountryVisaAdmin(admin.ModelAdmin):
    list_display = ['member', 'country', 'visa_type', 'number', 'expiry']
    list_filter = ['visa_type', 'country']
    search_fields = ['member__name', 'country', 'number']


@admin.register(CompanyProperty)
class CompanyPropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'serial_number', 'assigned_to', 'assigned_on', 'value', 'status']
    list_filter = ['category', 'status', 'assigned_to']
    search_fields = ['name', 'serial_number', 'assigned_to__emp_name']


@admin.register(PropertyCategory)
class PropertyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ['ref_no', 'memo_type', 'to_text', 'subject', 'memo_date']
    list_filter = ['memo_type', 'memo_date']
    search_fields = ['ref_no', 'subject', 'to_text', 'body']


@admin.register(MemoType)
class MemoTypeAdmin(admin.ModelAdmin):
    list_display = ['memo_type']
    search_fields = ['memo_type']


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