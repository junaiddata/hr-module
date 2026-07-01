from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField

class Mol(models.Model):
    mol= models.CharField(max_length=100, unique=True)

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
    eid_number = models.CharField(max_length=20, null=True, blank=True)
    labour_card_number = models.CharField(max_length=20, null=True, blank=True)
    insurance_number = models.CharField(max_length=50, null=True, blank=True)
    driving_license_number = models.CharField(max_length=30, null=True, blank=True)

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

    class Meta:
        ordering = ['-expected_from']

    def __str__(self):
        return f"{self.employee.emp_name} - {self.leave_type.name} ({self.expected_from} to {self.expected_to})"
    

class SalaryStructure(models.Model):
    employee  = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    basic     = models.FloatField(default=0)
    hra       = models.FloatField(default=0)
    transport = models.FloatField(default=0)
    others    = models.FloatField(default=0)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return self.basic + self.hra + self.transport + self.others

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
    def total_deductions(self):
        return sum(e.total_deductions for e in self.entries.all())


class PayrollEntry(models.Model):
    payroll_run    = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name='entries')
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_entries')

    # Snapshot of salary structure at run time
    basic          = models.FloatField(default=0)
    hra            = models.FloatField(default=0)
    transport      = models.FloatField(default=0)
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
        return self.loan_deduction + self.other_deductions + self.advance_deduction

    def compute_and_save(self):
        self.gross_salary = self.basic + self.hra + self.transport + self.others
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


class ChangeLog(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

# models.py
class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)

    def soft_delete(self):
        self.is_read = True
        self.save()

