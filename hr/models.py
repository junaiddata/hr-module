from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField

class Mol(models.Model):
    mol = models.CharField(max_length=100, unique=True)

    # Company info
    established_year = models.IntegerField(null=True, blank=True)

    # Payroll / WPS details
    company_code = models.CharField(max_length=50, blank=True, null=True)
    wps_number   = models.CharField(max_length=50, blank=True, null=True)
    iban         = models.CharField(max_length=34, blank=True, null=True)

    # Trade License
    trade_license_number = models.CharField(max_length=100, blank=True, null=True)
    trade_license_expiry = models.DateField(null=True, blank=True)
    license_document     = models.FileField(upload_to='mol_documents/licenses/', null=True, blank=True)

    # Tenancy Contract
    tenancy_contract        = models.FileField(upload_to='mol_documents/tenancy/', null=True, blank=True)
    tenancy_contract_expiry = models.DateField(null=True, blank=True)

    # Establishment Card
    establishment_card        = models.FileField(upload_to='mol_documents/establishment/', null=True, blank=True)
    establishment_card_expiry = models.DateField(null=True, blank=True)

    @property
    def trade_license_days_left(self):
        if self.trade_license_expiry:
            from django.utils import timezone
            return (self.trade_license_expiry - timezone.now().date()).days
        return None

    @property
    def tenancy_days_left(self):
        if self.tenancy_contract_expiry:
            from django.utils import timezone
            return (self.tenancy_contract_expiry - timezone.now().date()).days
        return None

    @property
    def establishment_card_days_left(self):
        if self.establishment_card_expiry:
            from django.utils import timezone
            return (self.establishment_card_expiry - timezone.now().date()).days
        return None

    def __str__(self):
        return self.mol

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_support_staff = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Role(models.Model):
    role_choices = [
        ('Head', 'Head'),
        ('MD', 'MD'),
        ('HR', 'HR'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role', null=True, blank=True)
    role = models.CharField(max_length=20, choices=role_choices)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        dept = f" ({self.department.name})" if self.department else ""
        return f"{self.role}{dept} - {self.user.username if self.user else 'No User Assigned'}"

class Employee(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    EMPLOYEE_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('On Leave', 'On Leave'),
        ('Resigned', 'Resigned'),
        ('Terminated', 'Terminated') ]
    PASSPORT_STATUS_CHOICES = [
        ('With company', 'With Company'),
        ('With employee', 'With Employee'),
    ]
    

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee')

    # Personal Info
    emp_name = models.CharField(max_length=100)
    emp_id = models.CharField(max_length=20, unique=True)
    photo = models.ImageField(upload_to='employee_photos/', null=True, blank=True)

    # Personal Details
    dob = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES,default='M')
    nationality = CountryField(default='IN')
    contact_number = models.CharField(max_length=20, null=True, blank=True)

    # Job Info
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    mol = models.ForeignKey(Mol, on_delete=models.SET_NULL, null=True)  # to which subcompany the employee visa belongs
    joining_date = models.DateField(null=True, blank=True)
    emp_salary = models.FloatField(null=True, blank=True)  # Monthly salary
    job_location = models.CharField(max_length=100, null=True, blank=True)
    employee_status = models.CharField(max_length=20, choices=EMPLOYEE_STATUS_CHOICES, default='Active')
    is_active = models.BooleanField(default=True)

    # Documents
    passport = models.FileField(upload_to='documents/passports/', null=True, blank=True)
    visa = models.FileField(upload_to='documents/visas/', null=True, blank=True)
    labour_card = models.FileField(upload_to='documents/labour_cards/', null=True, blank=True)
    eid = models.FileField(upload_to='documents/eids/', null=True, blank=True)
    insurance = models.FileField(upload_to='documents/insurance/', null=True, blank=True)
    driving_license = models.FileField(upload_to='documents/driving_licenses/', null=True, blank=True)
    passport_status = models.CharField(max_length=20, choices=PASSPORT_STATUS_CHOICES, default='With company')

    # Document details
    passport_number = models.CharField(max_length=20, null=True, blank=True)
    visa_number = models.CharField(max_length=30, null=True, blank=True)
    eid_number = models.CharField(max_length=20, null=True, blank=True)
    labour_card_number = models.CharField(max_length=20, null=True, blank=True)
    labour_number = models.CharField(max_length=30, null=True, blank=True)  # Labour No. — distinct from labour card no.
    insurance_number = models.CharField(max_length=50, null=True, blank=True)
    driving_license_number = models.CharField(max_length=30, null=True, blank=True)

    # Bank Details
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    iban = models.CharField(max_length=34, null=True, blank=True)
    routing_code = models.CharField(max_length=20, null=True, blank=True)

    # Expiry Dates for Alerts
    visa_expiry = models.DateField(null=True, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    labour_card_expiry = models.DateField(null=True, blank=True)
    eid_expiry = models.DateField(null=True, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    driving_license_expiry = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.emp_name

class LeaveType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., Annual, Sick, Emergency
    def __str__(self):
        return self.name


class Leave(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Head_Approved', 'Head Approved'),
        ('MD_Approved', 'MD Approved'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True)
    expected_from = models.DateField()
    expected_to = models.DateField()
    reported_to = models.CharField(max_length=100)
    days = models.IntegerField(default=0)
    actual_from = models.DateField(null=True, blank=True)
    actual_to = models.DateField(null=True, blank=True)
    actual_days = models.IntegerField(default=0)
    rejoined_on = models.DateField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # Stage 1: Department Head
    head_approved_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='head_approved_leaves'
    )
    head_approved_at = models.DateTimeField(null=True, blank=True)

    # Stage 2: Manager
    manager_approved_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='manager_approved_leaves'
    )
    manager_approved_at = models.DateTimeField(null=True, blank=True)

    # Stage 3: MD
    md_approved_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='md_approved_leaves'
    )
    md_approved_at = models.DateTimeField(null=True, blank=True)

    # Stage 4: HR (final)
    approved_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves'
    )

    rejection_reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    leave_application = models.FileField(upload_to='leave_applications/', null=True, blank=True)

    # Set when a Head/HR corrects the employee-requested dates during approval,
    # so the employee can see who changed their dates and what was requested originally.
    original_expected_from = models.DateField(null=True, blank=True)
    original_expected_to = models.DateField(null=True, blank=True)
    dates_changed_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='date_changed_leaves'
    )
    dates_changed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-expected_from']

    def __str__(self):
        return f"{self.employee.emp_name} - {self.leave_type.name} ({self.expected_from} to {self.expected_to})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present',  'Present'),
        ('absent',   'Absent'),
        ('half_day', 'Half Day'),
        ('leave',    'Leave'),
        ('holiday',  'Holiday'),
        ('week_off', 'Week Off'),
    ]
    SOURCE_CHOICES = [
        ('self',       'Self check-in'),
        ('hr',         'HR entry'),
        ('head',       'Head entry'),
        ('leave_auto', 'Approved leave'),
    ]
    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date       = models.DateField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, blank=True)
    check_in   = models.TimeField(null=True, blank=True)
    remarks    = models.CharField(max_length=255, blank=True, default='')
    source     = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='hr')
    marked_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_attendances')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.emp_name} — {self.date} — {self.get_status_display()}"


class BirthdayWish(models.Model):
    """Log of WhatsApp birthday wishes — one row per employee per year, so the
    daily job is idempotent and HR can see what was sent (or why it failed)."""
    STATUS_CHOICES = [('sent', 'Sent'), ('failed', 'Failed')]

    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='birthday_wishes')
    year       = models.IntegerField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    to_number  = models.CharField(max_length=30, blank=True, default='')
    message_id = models.CharField(max_length=128, blank=True, default='')
    error      = models.TextField(blank=True, default='')
    sent_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_birthday_wishes')
    sent_at    = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'year')
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.employee.emp_name} — {self.year} — {self.get_status_display()}"


class SalaryStructure(models.Model):
    employee  = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    basic     = models.FloatField(default=0)
    hra       = models.FloatField(default=0)
    transport = models.FloatField(default=0)
    fuel      = models.FloatField(default=0)
    others    = models.FloatField(default=0)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return self.basic + self.hra + self.transport + self.fuel + self.others

    def __str__(self):
        return f"Salary Structure – {self.employee.emp_name}"


class PayrollRun(models.Model):
    STATUS_CHOICES = [('Draft', 'Draft'), ('Confirmed', 'Confirmed')]
    MONTH_CHOICES  = [
        (1,'January'),(2,'February'),(3,'March'),(4,'April'),
        (5,'May'),(6,'June'),(7,'July'),(8,'August'),
        (9,'September'),(10,'October'),(11,'November'),(12,'December'),
    ]
    month        = models.IntegerField(choices=MONTH_CHOICES)
    year         = models.IntegerField()
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Draft')
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='payroll_runs')
    created_at   = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes        = models.TextField(blank=True)

    class Meta:
        unique_together = ('month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Payroll {self.get_month_display()} {self.year}"

    @property
    def total_gross(self):
        return sum(e.gross_salary for e in self.entries.all())

    @property
    def total_net(self):
        return sum(e.net_salary for e in self.entries.all())

    @property
    def total_additions(self):
        return sum(e.total_additions for e in self.entries.all())

    # --- Monthly deduction breakdown (run level) ---
    @property
    def total_loan_deductions(self):
        return sum(e.loan_deduction for e in self.entries.all())

    @property
    def total_advance_deductions(self):
        return sum(e.advance_deduction for e in self.entries.all())

    @property
    def total_other_deductions(self):
        return sum(e.other_deductions for e in self.entries.all())

    @property
    def total_attendance_deductions(self):
        return sum(e.attendance_deduction for e in self.entries.all())

    @property
    def total_deductions(self):
        return sum(e.total_deductions for e in self.entries.all())


class PayrollEntry(models.Model):
    payroll_run    = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='entries')
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_entries')

    # Snapshot of salary structure at run time
    basic          = models.FloatField(default=0)
    hra            = models.FloatField(default=0)
    transport      = models.FloatField(default=0)
    fuel           = models.FloatField(default=0)
    others         = models.FloatField(default=0)

    # Additions
    bonus          = models.FloatField(default=0)
    overtime_pay   = models.FloatField(default=0)
    other_additions= models.FloatField(default=0)

    # Deductions
    loan_deduction    = models.FloatField(default=0)
    other_deductions  = models.FloatField(default=0)
    advance_deduction = models.FloatField(default=0)
    advance_salary    = models.ForeignKey(
        'AdvanceSalary', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payroll_deductions'
    )

    # Attendance-based deduction (absent days / half days)
    absent_days          = models.IntegerField(default=0)
    half_days            = models.IntegerField(default=0)
    attendance_deduction = models.FloatField(default=0)

    # Computed (stored for reporting)
    gross_salary   = models.FloatField(default=0)
    net_salary     = models.FloatField(default=0)

    notes          = models.TextField(blank=True)

    class Meta:
        unique_together = ('payroll_run', 'employee')

    def __str__(self):
        return f"{self.employee.emp_name} – {self.payroll_run}"

    @property
    def total_additions(self):
        return self.bonus + self.overtime_pay + self.other_additions

    @property
    def total_deductions(self):
        return self.loan_deduction + self.other_deductions + self.advance_deduction + self.attendance_deduction

    def compute_and_save(self):
        self.gross_salary = self.basic + self.hra + self.transport + self.fuel + self.others
        self.net_salary   = self.gross_salary + self.total_additions - self.total_deductions
        self.save()


class AdvanceSalary(models.Model):
    STATUS_CHOICES = [
        ('Pending',      'Pending'),
        ('Head_Approved','Head Approved'),
        ('Approved',     'Approved'),
        ('Rejected',     'Rejected'),
    ]

    employee                    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='advance_salaries')
    amount                      = models.FloatField()
    reason                      = models.TextField()
    requested_monthly_deduction = models.FloatField(default=0)
    approved_monthly_deduction  = models.FloatField(null=True, blank=True)

    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    head_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='head_approved_advances')
    head_approved_at = models.DateTimeField(null=True, blank=True)

    hr_approved_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_approved_advances')
    hr_approved_at   = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(null=True, blank=True)
    applied_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_advances')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def effective_monthly_deduction(self):
        return self.approved_monthly_deduction if self.approved_monthly_deduction else self.requested_monthly_deduction

    @property
    def monthly_deduction(self):
        return self.effective_monthly_deduction

    @property
    def total_deducted(self):
        from django.db.models import Sum
        result = PayrollEntry.objects.filter(
            advance_salary=self,
            payroll_run__status='Confirmed'
        ).aggregate(total=Sum('advance_deduction'))['total']
        return round(result or 0, 2)

    @property
    def remaining_amount(self):
        return round(max(0, self.amount - self.total_deducted), 2)

    @property
    def estimated_months(self):
        import math
        ded = self.effective_monthly_deduction
        if ded and ded > 0:
            return math.ceil(self.amount / ded)
        return 0

    @property
    def progress_pct(self):
        if self.amount > 0:
            return min(100, round(self.total_deducted / self.amount * 100, 1))
        return 0

    @property
    def is_fully_repaid(self):
        return self.remaining_amount <= 0

    @property
    def was_deduction_changed(self):
        """True if the effective deduction differs from what the employee requested."""
        return bool(self.approved_monthly_deduction) and round(self.approved_monthly_deduction, 2) != round(self.requested_monthly_deduction, 2)

    def set_monthly_deduction(self, new_amount, user, role_label, note=''):
        """Update the approved monthly deduction and record a change-log entry."""
        old = self.approved_monthly_deduction if self.approved_monthly_deduction else self.requested_monthly_deduction
        new_amount = round(float(new_amount), 2)
        self.approved_monthly_deduction = new_amount
        self.save(update_fields=['approved_monthly_deduction', 'updated_at'])
        # Only log if it actually changed
        if round(old or 0, 2) != new_amount:
            AdvanceDeductionChange.objects.create(
                advance=self,
                old_amount=old,
                new_amount=new_amount,
                changed_by=user,
                changed_by_role=role_label,
                note=note,
            )
        return self

    def __str__(self):
        return f"{self.employee.emp_name} — Advance {self.amount} ({self.status})"


class AdvanceDeductionChange(models.Model):
    """Audit trail for every change to an advance's monthly deduction amount."""
    advance         = models.ForeignKey(AdvanceSalary, on_delete=models.CASCADE, related_name='deduction_changes')
    old_amount      = models.FloatField(null=True, blank=True)
    new_amount      = models.FloatField()
    changed_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='advance_deduction_changes')
    changed_by_role = models.CharField(max_length=20, blank=True)  # Head / HR
    note            = models.TextField(blank=True)
    changed_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['changed_at']

    def __str__(self):
        return f"{self.advance.employee.emp_name}: {self.old_amount} → {self.new_amount} by {self.changed_by_role}"


class PassportRequest(models.Model):
    """Employee requests temporary custody of their passport; HR approves."""
    STATUS_CHOICES = [
        ('Pending',  'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Returned', 'Returned'),
    ]

    employee        = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='passport_requests')
    reason          = models.TextField()
    needed_from     = models.DateField(null=True, blank=True)
    expected_return = models.DateField(null=True, blank=True)

    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    approved_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_passport_requests')
    approved_at     = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)

    returned_at        = models.DateTimeField(null=True, blank=True)
    returned_marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='returned_passport_requests')

    applied_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_passport_requests')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def is_outstanding(self):
        """Approved and not yet returned — passport is currently with the employee."""
        return self.status == 'Approved'

    def __str__(self):
        return f"{self.employee.emp_name} — Passport Request ({self.status})"


class SalaryRevision(models.Model):
    """Audit trail for every salary change (increment / decrement / adjustment)."""
    CHANGE_TYPE_CHOICES = [
        ('Increment',  'Increment'),
        ('Decrement',  'Decrement'),
        ('Adjustment', 'Adjustment'),
    ]
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salary_revisions')
    change_type    = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    effective_date = models.DateField()

    # Snapshot of values before this revision
    old_salary    = models.FloatField(null=True, blank=True)
    old_basic     = models.FloatField(default=0)
    old_hra       = models.FloatField(default=0)
    old_transport = models.FloatField(default=0)
    old_fuel      = models.FloatField(default=0)
    old_others    = models.FloatField(default=0)

    # Values applied by this revision
    new_salary    = models.FloatField()
    new_basic     = models.FloatField(default=0)
    new_hra       = models.FloatField(default=0)
    new_transport = models.FloatField(default=0)
    new_fuel      = models.FloatField(default=0)
    new_others    = models.FloatField(default=0)

    reason     = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='salary_revisions')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date', '-changed_at']

    @property
    def difference(self):
        return round((self.new_salary or 0) - (self.old_salary or 0), 2)

    def __str__(self):
        return f"{self.employee.emp_name} — {self.change_type} ({self.effective_date})"


class ChangeLog(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

# models.py
class Notification(models.Model):
    URGENCY_CHOICES = [
        ('critical', 'Critical'),
        ('warning',  'Warning'),
        ('info',     'Info'),
    ]
    title      = models.CharField(max_length=255)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    employee   = models.ForeignKey('Employee', on_delete=models.CASCADE, null=True, blank=True)
    is_read    = models.BooleanField(default=False)

    # Document-expiry specific fields
    category = models.CharField(max_length=50, blank=True, default='')   # 'document_expiry' / 'mol_document_expiry' / 'vehicle_document_expiry'
    urgency  = models.CharField(max_length=20, blank=True, default='info', choices=URGENCY_CHOICES)
    doc_type = models.CharField(max_length=50, blank=True, default='')   # 'VISA','EID','MOL_TRADE_LICENSE','MULKIYA',…
    mol      = models.ForeignKey('Mol', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    vehicle  = models.ForeignKey('Vehicle', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    management_member = models.ForeignKey('ManagementMember', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    class Meta:
        ordering = ['-created_at']

    def soft_delete(self):
        self.is_read = True
        self.save()


class OtherRecord(models.Model):
    """A general document store (HR/MD only). Each record has a heading, an
    optional comment and file, and can be linked to one or more employees —
    linked employees see it as a 'related document' on their detail page."""
    EXPENSE_CHOICES = [
        ('visa',      'Visa Expense'),
        ('vehicle',   'Vehicle'),
        ('office',    'Office'),
        ('marketing', 'Marketing'),
        ('it',        'IT'),
        ('general',   'General'),
        ('other',     'Other'),
    ]

    title       = models.CharField(max_length=200)
    comment     = models.TextField(blank=True, default='')
    document    = models.FileField(upload_to='other_records/', null=True, blank=True)
    employees   = models.ManyToManyField(Employee, blank=True, related_name='other_records')

    # Expense classification. 'other' is free-text via expense_other.
    expense_category = models.CharField(max_length=20, choices=EXPENSE_CHOICES, blank=True, default='')
    expense_other    = models.CharField('Other expense (specify)', max_length=200, blank=True, default='')

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_other_records')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def expense_label(self):
        """Display label for the expense category; free-text for 'other'."""
        if not self.expense_category:
            return ''
        if self.expense_category == 'other':
            return self.expense_other or 'Other'
        return self.get_expense_category_display()


class MonthlyReview(models.Model):
    """A department head's monthly review of one employee under them.
    Ratings are 1–5. Only HR & MD can read reviews (the private 'concerns'
    field especially) — employees never see them."""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reviews')
    month      = models.IntegerField()
    year       = models.IntegerField()

    # Ratings (1–5)
    rating_task          = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)  # task completion / output
    rating_punctuality   = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)  # punctuality & attendance
    rating_quality       = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)  # quality of work
    rating_communication = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)  # responsiveness / communication

    went_well       = models.TextField(blank=True, default='')                 # optional, quick
    concerns        = models.TextField(blank=True, default='')                 # private — HR/MD only
    needs_attention = models.BooleanField(default=False)                       # flag for HR to scan

    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='given_reviews')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month', 'employee__emp_name']

    @property
    def ratings(self):
        return [r for r in (self.rating_task, self.rating_punctuality,
                            self.rating_quality, self.rating_communication) if r]

    @property
    def average(self):
        vals = self.ratings
        return round(sum(vals) / len(vals), 1) if vals else None

    def __str__(self):
        return f"{self.employee.emp_name} — {self.month:02d}/{self.year}"


class WeeklyReview(models.Model):
    """A department head's weekly review of an employee (week 1–5 within a
    month). Same fields as MonthlyReview; HR/MD only can read them."""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='weekly_reviews')
    year       = models.IntegerField()
    month      = models.IntegerField()
    week       = models.IntegerField()   # 1–5 within the month

    rating_task          = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_punctuality   = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_quality       = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_communication = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)

    went_well       = models.TextField(blank=True, default='')
    concerns        = models.TextField(blank=True, default='')
    needs_attention = models.BooleanField(default=False)

    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='given_weekly_reviews')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'year', 'month', 'week')
        ordering = ['-year', '-month', 'week', 'employee__emp_name']

    @property
    def ratings(self):
        return [r for r in (self.rating_task, self.rating_punctuality,
                            self.rating_quality, self.rating_communication) if r]

    @property
    def average(self):
        vals = self.ratings
        return round(sum(vals) / len(vals), 1) if vals else None

    def __str__(self):
        return f"{self.employee.emp_name} — W{self.week} {self.month:02d}/{self.year}"


class Vehicle(models.Model):
    """Fleet register (HR/MD only). Tracks company- and personally-owned
    vehicles: registration, tracking device, mulkiya (registration card) and
    its expiry, mortgage/finance status, etc."""
    OWNERSHIP_CHOICES = [
        ('Company',  'Company Vehicle'),
        ('Personal', 'Personal Vehicle'),
    ]

    ownership       = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, default='Company')
    name            = models.CharField('Name', max_length=200)
    car_number      = models.CharField('Car Number', max_length=50)
    model           = models.CharField('Model', max_length=100, blank=True, default='')
    tracking        = models.CharField('Tracking', max_length=100, blank=True, default='')
    tracking_exp_date = models.DateField('Tracking Exp Date', null=True, blank=True)
    state           = models.CharField('State', max_length=100, blank=True, default='')
    traffic_code    = models.CharField('Traffic Code', max_length=100, blank=True, default='')
    mortgage        = models.CharField('Mortgage', max_length=150, blank=True, default='')
    car_and_model   = models.CharField('Car and Model', max_length=200, blank=True, default='')
    company         = models.CharField('Company', max_length=200, blank=True, default='')
    mulkiya_expiry  = models.DateField('Mulkiya Expiry', null=True, blank=True)
    mulkiya_document = models.FileField('Mulkiya Document', upload_to='vehicles/mulkiya/', null=True, blank=True)

    # Some vehicles are assigned to / associated with a specific employee.
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')

    # Sale / disposal record — filled in by HR when a vehicle is sold.
    is_sold       = models.BooleanField('Sold', default=False)
    sold_on       = models.DateField('Sold On', null=True, blank=True)
    sold_amount   = models.DecimalField('Sold Amount', max_digits=12, decimal_places=2, null=True, blank=True)
    sold_to       = models.CharField('Sold To', max_length=200, blank=True, default='')
    sold_document = models.FileField('Sale Document', upload_to='vehicles/sold/', null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_vehicles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.car_number})"

    def last_service_dates(self):
        """Most-recent completed service date per type — the vehicle's service
        history ('previous dates'). Returns a dict of service_type -> date."""
        result = {}
        for svc in self.services.filter(status='Completed', service_date__isnull=False):
            cur = result.get(svc.service_type)
            if cur is None or svc.service_date > cur:
                result[svc.service_type] = svc.service_date
        return result

    @property
    def pending_service_count(self):
        return self.services.filter(status='Requested').count()

    @property
    def latest_odometer(self):
        return self.odometer_readings.first()


class VehicleService(models.Model):
    """A service / maintenance record for a Vehicle.

    Serves two purposes:
      1. HISTORY — each completed record stores the date a service was performed,
         giving the vehicle a maintenance log of previous service dates.
      2. REQUEST workflow — an employee assigned to a vehicle can request a
         service (General Service, Tyre Change or Other). HR/MD then approve &
         complete it (recording the service date) or reject it.
    """
    SERVICE_TYPE_CHOICES = [
        ('general', 'General Service'),
        ('tyre',    'Tyre Change'),
        ('battery', 'Battery'),
        ('major',   'Major Service'),
        ('other',   'Other'),
    ]
    # Service types a self-service employee is allowed to request.
    EMPLOYEE_REQUESTABLE = ['general', 'tyre', 'battery', 'major', 'other']

    STATUS_CHOICES = [
        ('Requested', 'Requested'),
        ('Approved',  'Approved'),
        ('Completed', 'Completed'),
        ('Rejected',  'Rejected'),
    ]

    vehicle      = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='services')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    other_detail = models.CharField('Other (specify)', max_length=200, blank=True, default='')

    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Requested')
    service_date = models.DateField('Service Date', null=True, blank=True)
    notes        = models.TextField(blank=True, default='')
    cost         = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Who requested it (employee self-service) and who logged it (HR/MD).
    requested_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicle_service_requests')
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logged_vehicle_services')

    approved_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_vehicle_services')
    approved_at      = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')

    # Cost approval — after the employee completes the service and records the
    # cost, HR signs off (approves) that cost.
    cost_approved    = models.BooleanField(default=False)
    cost_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cost_approved_vehicle_services')
    cost_approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-service_date', '-created_at']

    def __str__(self):
        return f"{self.get_service_type_display()} — {self.vehicle.name}"

    @property
    def type_label(self):
        """Human label; falls back to the free-text detail for 'Other'."""
        if self.service_type == 'other' and self.other_detail:
            return self.other_detail
        return self.get_service_type_display()

    @property
    def awaiting_cost_approval(self):
        """Completed with a cost recorded but HR hasn't approved the cost yet."""
        return self.status == 'Completed' and self.cost is not None and not self.cost_approved


class VehicleOdometerReading(models.Model):
    """A logged odometer (mileage) reading for a Vehicle, building up a history
    of distance travelled over time."""
    vehicle      = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='odometer_readings')
    reading_km   = models.PositiveIntegerField('Odometer Reading (km)')
    reading_date = models.DateField('Reading Date')
    notes        = models.CharField(max_length=200, blank=True, default='')

    recorded_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logged_odometer_readings')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reading_date', '-created_at']

    def __str__(self):
        return f"{self.vehicle.name} — {self.reading_km} km ({self.reading_date})"


class ManagementMember(models.Model):
    """A company management person (owner / director / partner) or one of their
    family members. Stores personal documents — Emirates ID, Passport, Driving
    License and Visa (with a visa type) — plus a travel history. HR/MD only."""

    RELATION_CHOICES = [
        ('self',     'Management'),
        ('spouse',   'Spouse'),
        ('son',      'Son'),
        ('daughter', 'Daughter'),
        ('father',   'Father'),
        ('mother',   'Mother'),
        ('other',    'Other'),
    ]

    VISA_TYPE_CHOICES = [
        ('employment', 'Employment Visa'),
        ('residence',  'Residence Visa'),
        ('investor',   'Investor Visa'),
        ('partner',    'Partner Visa'),
        ('golden',     'Golden Visa'),
        ('green',      'Green Visa'),
        ('family',     'Family / Dependent Visa'),
        ('visit',      'Visit Visa'),
        ('tourist',    'Tourist Visa'),
        ('mission',    'Mission Visa'),
        ('student',    'Student Visa'),
        ('retirement', 'Retirement Visa'),
        ('other',      'Other'),
    ]

    # Family link: null head = a management person; set = a family member.
    head        = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='family')
    relation    = models.CharField(max_length=20, choices=RELATION_CHOICES, default='self')

    name        = models.CharField('Full Name', max_length=200)
    designation = models.CharField('Designation / Role', max_length=150, blank=True, default='')
    nationality = models.CharField(max_length=100, blank=True, default='')
    dob         = models.DateField('Date of Birth', null=True, blank=True)
    phone       = models.CharField(max_length=40, blank=True, default='')
    email       = models.EmailField(blank=True, default='')
    photo       = models.ImageField(upload_to='management/photos/', null=True, blank=True)

    # Emirates ID
    eid_number   = models.CharField('Emirates ID Number', max_length=50, blank=True, default='')
    eid_expiry   = models.DateField('Emirates ID Expiry', null=True, blank=True)
    eid_document = models.FileField('Emirates ID Document', upload_to='management/eid/', null=True, blank=True)

    # Passport
    passport_number   = models.CharField('Passport Number', max_length=50, blank=True, default='')
    passport_expiry   = models.DateField('Passport Expiry', null=True, blank=True)
    passport_document = models.FileField('Passport Document', upload_to='management/passport/', null=True, blank=True)

    # Driving License
    dl_number   = models.CharField('Driving License Number', max_length=50, blank=True, default='')
    dl_expiry   = models.DateField('Driving License Expiry', null=True, blank=True)
    dl_document = models.FileField('Driving License Document', upload_to='management/dl/', null=True, blank=True)

    # Visa
    visa_type     = models.CharField('Visa Type', max_length=20, choices=VISA_TYPE_CHOICES, blank=True, default='')
    visa_number   = models.CharField('Visa Number', max_length=50, blank=True, default='')
    visa_expiry   = models.DateField('Visa Expiry', null=True, blank=True)
    visa_document = models.FileField('Visa Document', upload_to='management/visa/', null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_management')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_family(self):
        return self.head_id is not None

    @property
    def visa_type_label(self):
        return self.get_visa_type_display() if self.visa_type else ''


class TravelRecord(models.Model):
    """A single trip for a management member — its travel history."""
    member         = models.ForeignKey(ManagementMember, on_delete=models.CASCADE, related_name='travels')
    destination    = models.CharField(max_length=150)
    purpose        = models.CharField(max_length=200, blank=True, default='')
    departure_date = models.DateField(null=True, blank=True)
    return_date    = models.DateField(null=True, blank=True)
    notes          = models.TextField(blank=True, default='')
    document       = models.FileField('Travel Document', upload_to='management/travel/', null=True, blank=True)
    created_by     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_travels')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-departure_date', '-created_at']

    def __str__(self):
        return f"{self.member.name} → {self.destination}"


class CountryVisa(models.Model):
    """A visa a management member holds for a country other than the UAE
    (e.g. US, UK, Schengen). Separate from the primary UAE visa on the member."""
    VISA_TYPE_CHOICES = [
        ('tourist',   'Tourist'),
        ('visit',     'Visit'),
        ('business',  'Business'),
        ('work',      'Work'),
        ('student',   'Student'),
        ('residence', 'Residence'),
        ('transit',   'Transit'),
        ('other',     'Other'),
    ]

    member     = models.ForeignKey(ManagementMember, on_delete=models.CASCADE, related_name='country_visas')
    country    = models.CharField(max_length=100)
    visa_type  = models.CharField('Visa Type', max_length=20, choices=VISA_TYPE_CHOICES, blank=True, default='')
    number     = models.CharField('Visa Number', max_length=50, blank=True, default='')
    issue_date = models.DateField('Issue Date', null=True, blank=True)
    expiry     = models.DateField('Expiry', null=True, blank=True)
    document   = models.FileField('Visa Document', upload_to='management/country_visa/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_country_visas')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['country', '-expiry']

    def __str__(self):
        return f"{self.member.name} — {self.country} visa"

    @property
    def visa_type_label(self):
        return self.get_visa_type_display() if self.visa_type else ''


class CompanyProperty(models.Model):
    """A company-owned asset/property that can be assigned to an employee.
    When assigned, it appears on that employee's detail page. HR/MD only."""
    CATEGORY_CHOICES = [
        ('laptop',    'Laptop'),
        ('desktop',   'Desktop'),
        ('phone',     'Phone'),
        ('sim',       'SIM Card'),
        ('tablet',    'Tablet'),
        ('furniture', 'Furniture'),
        ('equipment', 'Equipment'),
        ('tool',      'Tool'),
        ('other',     'Other'),
    ]

    name          = models.CharField('Property Name', max_length=200)
    category      = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, default='')
    serial_number = models.CharField('Serial / Asset No.', max_length=100, blank=True, default='')
    description   = models.TextField(blank=True, default='')
    purchase_date = models.DateField(null=True, blank=True)
    value         = models.DecimalField('Value (AED)', max_digits=12, decimal_places=2, null=True, blank=True)
    document      = models.FileField('Document', upload_to='properties/', null=True, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')
    assigned_on = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Company properties'

    def __str__(self):
        return self.name

    @property
    def category_label(self):
        return self.get_category_display() if self.category else ''


class MemoType(models.Model):
    """A memo type/category, created by HR/MD, offered as a dropdown when issuing a Memo."""
    memo_type = models.CharField('Memo Type', max_length=60, unique=True)

    class Meta:
        ordering = ['memo_type']

    def __str__(self):
        return self.memo_type


class Memo(models.Model):
    """An official memorandum issued on the company letterhead and rendered to a
    PDF. HR/MD only."""

    memo_type   = models.ForeignKey(MemoType, on_delete=models.PROTECT, related_name='memos')
    ref_no      = models.CharField('Reference No.', max_length=60, blank=True, default='')
    to_text     = models.CharField('To', max_length=200, default='All Staff')
    employee    = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='memos')
    department  = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='memos')
    memo_date   = models.DateField()
    subject     = models.CharField('Subject (Re)', max_length=300)
    body        = models.TextField()
    signatory   = models.CharField(max_length=120, default='HR/ADMIN DIVISION')
    signature   = models.ImageField(upload_to='memos/signatures/', null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_memos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-memo_date', '-created_at']

    def __str__(self):
        return f"{self.ref_no or 'Memo'} — {self.subject}"
