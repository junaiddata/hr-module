# HR Module — Complete System Workflow

> Project: Django HR Management System
> Stack: Python / Django · SQLite · Bootstrap 5 · Font Awesome
> App: `hr` (single-app inside `hr_module` project)

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [User Roles](#2-user-roles)
3. [Authentication Flow](#3-authentication-flow)
4. [Employee Management](#4-employee-management)
5. [Department Management](#5-department-management)
6. [Leave Management — Full Workflow](#6-leave-management--full-workflow)
7. [Head Portal Workflow](#7-head-portal-workflow)
8. [MD Portal Workflow](#8-md-portal-workflow)
9. [HR Portal Workflow](#9-hr-portal-workflow)
10. [System Settings](#10-system-settings)
11. [Data Models Reference](#11-data-models-reference)
12. [URL Reference](#12-url-reference)

---

## 1. System Architecture

```
hr_module/
├── hr_module/          # Django project config (settings, urls)
├── hr/                 # Single app
│   ├── models.py       # All data models
│   ├── views.py        # All views / business logic
│   ├── urls.py         # All URL patterns
│   ├── admin.py        # Django admin registration
│   ├── migrations/     # Database migration history
│   └── templates/
│       └── hr_de/      # All active templates (modern UI)
├── static/             # CSS, JS, images
├── media/              # Uploaded files (leave docs, employee photos)
└── db.sqlite3          # Database
```

### Key Design Decisions

| Decision | Reason |
|---|---|
| Single `hr` app | Keeps the project simple; no cross-app complexity |
| `Role` as a separate model (not a field) | Allows clean `request.user.role.role` checks; OneToOne with User |
| MD has no `Employee` record | MD is a system account, not a staff member |
| Support staff dept flag | Drives the leave approval fast-track (skip MD stage) |
| `emp_salary` field on Employee | Salary kept simple as a field; full Salary model removed |

---

## 2. User Roles

The system has **three roles**, set via the `Role` model:

```
User  ──OneToOne──►  Role (role = 'Head' | 'MD' | 'HR')
         │
         └──────────►  Employee (for Head accounts only)
```

### Role Capabilities Matrix

| Feature | HR | MD | Head |
|---|:---:|:---:|:---:|
| Add / Edit Employees | ✅ | ✗ | ✗ |
| Bulk Upload Employees | ✅ | ✗ | ✗ |
| View Employee List | ✅ | ✅ | Dept only |
| View Employee Detail | ✅ | ✅ | Dept only |
| Manage Departments | ✅ | ✗ | ✗ |
| Manage Leave Types | ✅ | ✗ | ✗ |
| Manage MD Accounts | ✅ | ✗ | ✗ |
| Manage MOL Records | ✅ | ✅ | ✗ |
| View Org Chart | ✅ | ✅ | ✅ |
| View All Leave History | ✅ | ✅ | Dept only |
| Approve Leaves (Head stage) | ✗ | ✗ | ✅ |
| Approve Leaves (MD stage) | ✗ | ✅ | ✗ |
| Approve Leaves (Final) | ✅ | ✗ | ✗ |
| Apply Leave on Employee's Behalf | ✗ | ✗ | ✅ |
| Set Employee Rejoining Date | ✗ | ✗ | ✅ |
| System (Notifications, Password) | ✅ | ✅ | ✅ |

---

## 3. Authentication Flow

```
User visits any URL
        │
        ▼
  @login_required ──► Not logged in ──► /login/
        │
        ▼ (logged in)
  login_view POST
        │
        ├── Has Role? ──► No ──► "No role assigned" error
        │
        ├── Role = 'HR'   ──► redirect → /  (HR Dashboard)
        ├── Role = 'MD'   ──► redirect → /  (MD Dashboard)
        └── Role = 'Head' ──► redirect → /employee/home/  (Head Dept Dashboard)
```

**Password Reset:** `/forgot-password/` — verifies username + date-of-birth, then allows password change without email.

---

## 4. Employee Management

### Create Employee (HR only)

```
/employee/add/
    │
    Form fields:
    ├── Personal: emp_name, emp_id, gender, dob, phone, email, address
    ├── Job: designation, department, joining_date, emp_salary
    ├── Documents: photo, emp_document
    └── Account: create_account (checkbox) → username, password
            │
            └── Creates Django User + Role(Head) if department is Head dept
                  OR plain User (employee login) if no role needed
```

### Edit Employee (HR only)
`/employee/<pk>/edit/` — same fields; updating `department` reassigns the employee's dept head.

### Bulk Upload (HR only)
`/employee-upload/` — CSV/Excel import. Maps columns to Employee fields, creates records in bulk.

### Employee Detail
`/employee/<pk>/` — viewable by HR, MD, and Head (own dept only).
Shows: personal info, leave summary, MOL records, salary field.

---

## 5. Department Management

`/departments/` — HR only.

Each department has:
- `name` — display name
- `is_support_staff` (Boolean) — **determines leave approval fast-track**

| `is_support_staff` | Effect on leave flow |
|---|---|
| `False` (regular dept) | Pending → Head_Approved → MD_Approved → Approved |
| `True` (support staff) | Pending → MD_Approved → Approved (Head + MD skipped when Head applies) |

---

## 6. Leave Management — Full Workflow

### Leave Status Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                       LEAVE STATUS FLOW                              │
│                                                                       │
│  Employee applies:         Pending                                    │
│                               │                                       │
│                        ┌──────┴──────┐                               │
│                        ▼             ▼                                │
│               Head approves     Head rejects                          │
│                        │             │                                │
│                  Head_Approved   Rejected ◄────────────────────────┐ │
│                        │                                            │ │
│                        ▼                                            │ │
│                  MD reviews ──────────────── MD rejects ───────────┘ │
│                        │                                              │
│                  MD_Approved                                          │
│                        │                                              │
│                        ▼                                              │
│                  HR reviews ──────────────── HR rejects ─────────────│
│                        │                                              │
│                    Approved                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Status Values

| Status | Meaning | Who can act next |
|---|---|---|
| `Pending` | Just applied, awaiting Head | Head |
| `Head_Approved` | Head approved, awaiting MD | MD |
| `MD_Approved` | MD approved, awaiting HR final | HR |
| `Approved` | Fully approved | — |
| `Rejected` | Rejected at any stage | — |

### Leave Fields

| Field | Description |
|---|---|
| `expected_from` | Start date of leave |
| `expected_to` | End date of leave (applied) |
| `days` | `(expected_to - expected_from).days + 1` |
| `rejoined_on` | Actual date employee rejoined (set by Head) |
| `actual_days` | `(rejoined_on - expected_from).days + 1` |
| `reason` | Employee's stated reason |
| `leave_application` | Uploaded document (optional) |
| `reported_to` | Who the employee reports to |
| `head_approved_by / at` | Head who approved + timestamp |
| `md_approved_by / at` | MD who approved + timestamp |
| `approved_by` | HR who gave final approval |
| `rejection_reason` | Filled if rejected |

---

## 7. Head Portal Workflow

Head accounts are linked to a **specific department** via `Role.department`.

### 7.1 Department Dashboard (`/employee/home/`)

Shows:
- Total employees in dept
- Pending approvals count
- Employee table with leave counts + action buttons
- Leaves pending Head approval (inline table)
- Recently approved leaves

### 7.2 Approve Pending Leaves

```
/leaves/approve/<id>/
        │
        ├── Leave status = 'Pending' → Head can Approve or Reject
        │         │
        │         ├── Approve → status = 'Head_Approved', head_approved_by = me, notify
        │         └── Reject  → status = 'Rejected', rejection_reason saved
        │
        └── (Other statuses shown as read-only pipeline view)
```

### 7.3 Apply Leave on Behalf of Employee

Any employee in the Head's department can have leave applied by the Head directly.

```
Head selects employee → /employee/<emp_pk>/apply-leave/
        │
        Fills:  leave_type, expected_from, expected_to,
                reason, document (optional),
                rejoined_on (optional — defaults to expected_to)
        │
        ▼
  dept.is_support_staff?
        │
        ├── YES → status = 'MD_Approved'   (skips Head + MD stages)
        │          Goes to HR for final approval
        │
        └── NO  → status = 'Head_Approved'  (skips Head stage)
                   Goes to MD for approval next
        │
        In both cases:
        head_approved_by = request.user
        head_approved_at = now()
        actual_days      = (rejoined_on - expected_from).days + 1
```

### 7.4 Set / Update Rejoining Date

After a leave is recorded, the Head can update the actual rejoining date at any time:

```
/leave/<leave_pk>/set-rejoining/
        │
        Head enters: rejoined_on (date)
        │
        actual_days = (rejoined_on - expected_from).days + 1
        │
        ├── rejoined_on > expected_to → Extended leave (actual_days > days)
        ├── rejoined_on = expected_to → Same as applied
        └── rejoined_on < expected_to → Early return (actual_days < days)
```

### 7.5 Leave History (Head)

`/leaves/history/` renders `leave_history_head.html` for Head role.
- Shows all leaves for the department
- Search by employee name / ID
- Filter by leave type
- Each row shows: applied days, status, rejoining date, actual days
- Action button: Set Rejoining / Update Rejoining per leave

---

## 8. MD Portal Workflow

MD is a **system account** — has a `User` + `Role(MD)` but **no Employee record**.
Created by HR from Settings → MD Accounts.

### MD can:
- View full employee list (read-only)
- View employee details
- View all leave history
- Approve/Reject `Head_Approved` leaves
- View org chart
- View / add / edit MOL records
- Manage notifications
- Change password

### MD Approval

```
/leaves/pending/   →  shows all Leave with status='Head_Approved'
        │
        MD reviews: /leaves/approve/<id>/
        │
        ├── Approve → status = 'MD_Approved', md_approved_by = me, notify
        └── Reject  → status = 'Rejected', rejection_reason saved
```

---

## 9. HR Portal Workflow

HR has full system access. HR is the final approver in the leave chain.

### 9.1 Final Leave Approval

```
/leaves/pending/   →  shows all Leave with status='MD_Approved'
        │
        HR reviews: /leaves/approve/<id>/
        │
        ├── Approve → status = 'Approved', approved_by = me, notify
        └── Reject  → status = 'Rejected', rejection_reason saved
```

### 9.2 Employee Management
- Add, edit, bulk-upload employees
- Assign departments and salary

### 9.3 Settings Panel (`/settings/`)

| Card | Function |
|---|---|
| Departments | Add/edit/delete departments, toggle support staff flag |
| Leave Types | Add/edit/delete leave categories (Annual, Sick, etc.) |
| MD Accounts | Create/delete MD system accounts |
| MOL Records | Ministry of Labor document tracking |
| Notifications | System notification management |
| Change Password | HR's own password |

---

## 10. System Settings

### MD Account Management (`/md-accounts/`)

HR creates MD accounts:
```
Form: full_name, username, password
      │
      Creates: User (first_name=full_name, no Employee record)
               Role(user=new_user, role='MD')
```

Deletion cascades: deleting the `User` removes the `Role` automatically.

### Notifications

- Auto-generated on leave status changes (approve/reject)
- `Notification` model: recipient (User), message, is_read, created_at
- Unread count shown in nav badge
- `/notifications/` lists all; `/notifications/<pk>/mark-read/` marks individual

---

## 11. Data Models Reference

### Role
```python
class Role(models.Model):
    ROLE_CHOICES = [('Head','Head'), ('MD','MD'), ('HR','HR')]
    user        = OneToOneField(User, related_name='role')
    role        = CharField(max_length=20, choices=ROLE_CHOICES)
    department  = ForeignKey(Department, null=True, blank=True)  # Head only
```

### Employee
```python
class Employee(models.Model):
    user          = OneToOneField(User, related_name='employee', null=True)
    emp_id        = CharField(unique=True)
    emp_name      = CharField()
    gender        = CharField()
    dob           = DateField(null=True)
    phone         = CharField()
    email         = EmailField()
    address       = TextField()
    designation   = CharField()
    department    = ForeignKey(Department)
    joining_date  = DateField(null=True)
    emp_salary    = FloatField(null=True)        # salary as a simple field
    photo         = ImageField(upload_to='photos/')
    emp_document  = FileField(upload_to='documents/')
    is_active     = BooleanField(default=True)
```

### Department
```python
class Department(models.Model):
    name             = CharField(unique=True)
    is_support_staff = BooleanField(default=False)  # drives approval fast-track
```

### Leave
```python
class Leave(models.Model):
    STATUS_CHOICES = [
        ('Pending','Pending'), ('Head_Approved','Head Approved'),
        ('MD_Approved','MD Approved'), ('Approved','Approved'),
        ('Rejected','Rejected'),
    ]
    employee         = ForeignKey(Employee)
    leave_type       = ForeignKey(LeaveType)
    expected_from    = DateField()
    expected_to      = DateField()
    days             = IntegerField(default=0)
    rejoined_on      = DateField(null=True, blank=True)
    actual_days      = IntegerField(default=0)
    reason           = TextField()
    reported_to      = CharField()
    leave_application= FileField(null=True)
    status           = CharField(choices=STATUS_CHOICES, default='Pending')
    head_approved_by = ForeignKey(User, null=True, related_name='head_approved')
    head_approved_at = DateTimeField(null=True)
    md_approved_by   = ForeignKey(User, null=True, related_name='md_approved')
    md_approved_at   = DateTimeField(null=True)
    approved_by      = ForeignKey(User, null=True, related_name='hr_approved')
    rejection_reason = TextField(blank=True)
    applied_on       = DateTimeField(auto_now_add=True)
```

### MOL
```python
class MOL(models.Model):
    employee    = ForeignKey(Employee)
    mol_number  = CharField()
    issue_date  = DateField()
    expiry_date = DateField()
    document    = FileField()
```

---

## 12. URL Reference

| URL | View | Access |
|---|---|---|
| `/` | `home` | All roles |
| `/login/` | `login_view` | Public |
| `/logout/` | `logout_view` | Logged in |
| `/forgot-password/` | `forgot_password` | Public |
| `/change-password/` | `change_password` | All roles |
| `/employee/home/` | `employee_home` | Head |
| `/employees/` | `employee_list` | HR, MD |
| `/employee/add/` | `employee_create` | HR |
| `/employee/<pk>/edit/` | `employee_edit` | HR |
| `/employee/<pk>/` | `employee_detail` | HR, MD, Head (own dept) |
| `/employee-upload/` | `bulk_upload_employees` | HR |
| `/employee/<emp_pk>/apply-leave/` | `apply_leave_behalf` | Head |
| `/leave/<leave_pk>/set-rejoining/` | `set_rejoining_date` | Head |
| `/leaves/add/` | `add_leave` | HR |
| `/leaves/history/` | `leave_history` | All roles |
| `/leaves/pending/` | `pending_leaves` | Head, MD, HR |
| `/leaves/approve/<id>/` | `approve_leave` | Head, MD, HR |
| `/leaves/<pk>/edit/` | `leave_edit` | HR |
| `/employee/<pk>/leaves/` | `employee_leave_detail` | HR, MD, Head |
| `/my-leaves/` | `my_leaves` | Employee login |
| `/my-leaves/apply/` | `submit_my_leave` | Employee login |
| `/departments/` | `department_list` | HR |
| `/department/add/` | `department_add` | HR |
| `/department/<pk>/edit/` | `department_edit` | HR |
| `/department/<pk>/delete/` | `department_delete` | HR |
| `/leave_types/` | `leave_type_list` | HR |
| `/leave_type/add/` | `leave_type_create` | HR |
| `/leave_type/<pk>/edit/` | `leave_type_edit` | HR |
| `/leave_type/<pk>/delete/` | `leave_type_delete` | HR |
| `/mols/` | `mol_list` | HR, MD |
| `/mol/add/` | `mol_add` | HR, MD |
| `/mol/<pk>/edit/` | `mol_edit` | HR, MD |
| `/mol/<pk>/delete/` | `mol_delete` | HR, MD |
| `/md-accounts/` | `md_account_list` | HR |
| `/md-accounts/create/` | `md_account_create` | HR |
| `/md-accounts/<pk>/delete/` | `md_account_delete` | HR |
| `/org-chart/` | `org_chart` | All roles |
| `/settings/` | `settings` | HR |
| `/notifications/` | `notification_list` | All roles |
| `/notifications/<pk>/mark-read/` | `mark_notification_read` | All roles |

---

*Last updated: June 2026*
