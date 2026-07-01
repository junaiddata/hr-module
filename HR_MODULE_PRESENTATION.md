# HR Module — System Presentation

---

## Slide 1 — Project Overview

### Django HR Management System

A web-based Human Resources module built with **Python / Django** to manage employees, departments, and multi-stage leave approvals — all within a single unified portal.

| Item | Detail |
|---|---|
| Framework | Django (Python) |
| Database | SQLite (SQLite → PostgreSQL ready) |
| Frontend | Bootstrap 5 + Font Awesome + Custom CSS |
| Architecture | Single-app Django project |
| Deployment | Local server (Django dev / Gunicorn + Nginx ready) |

---

## Slide 2 — What the System Does

**Three core pillars:**

```
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│   EMPLOYEE           │  │   LEAVE              │  │   ADMIN              │
│   MANAGEMENT         │  │   MANAGEMENT         │  │   SETTINGS           │
│                      │  │                      │  │                      │
│ • Add / Edit staff   │  │ • 3-stage approval   │  │ • Departments        │
│ • Bulk CSV upload    │  │ • Auto-approval by   │  │ • Leave Types        │
│ • Photo + Documents  │  │   Head (on behalf)   │  │ • MD Accounts        │
│ • Salary field       │  │ • Rejoining date     │  │ • MOL records        │
│ • MOL tracking       │  │   management         │  │ • Notifications      │
│ • Org chart view     │  │ • Real-time pipeline │  │ • Password mgmt      │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
```

---

## Slide 3 — User Roles

### Three distinct roles, one login system

```
                        Django User
                             │
                             ▼
                        Role Model
                    ┌────────┬────────┐
                    ▼        ▼        ▼
                  HEAD       MD       HR
```

| Role | Who | Description |
|---|---|---|
| **HR** | HR Manager | Full system access. Creates employees, manages settings, gives final leave approval. |
| **MD** | Managing Director | System account — no employee record. Views everything HR sees. Approves after Head. |
| **Head** | Department Head | Manages their department only. First-stage approver. Can apply leaves on behalf of staff. |

> **Key design:** MD has no Employee record — it is a pure system account created from Settings.

---

## Slide 4 — System Architecture

```
hr_module/
├── hr_module/          Django project config
├── hr/
│   ├── models.py       Role, Employee, Department, Leave,
│   │                   LeaveType, MOL, Notification
│   ├── views.py        All business logic (~900 lines)
│   ├── urls.py         All URL patterns (35+ routes)
│   └── templates/
│       └── hr_de/      Modern UI templates (base.html + pages)
├── static/             CSS, JS, branding
└── media/              Employee photos, documents, leave files
```

### Template System

All pages extend **`base.html`** which:
- Renders role-specific navigation automatically
- Handles user avatar, unread notification badge
- Provides consistent CSS variables across all pages

---

## Slide 5 — The Leave Approval Pipeline

### Standard 3-Stage Flow (Employee applies themselves)

```
  Employee          Head                MD               HR
  applies           reviews             reviews          reviews
     │                │                  │                │
     ▼                ▼                  ▼                ▼
  Pending  ──►  Head_Approved  ──►  MD_Approved  ──►  Approved
                     │                  │                │
                  Rejected           Rejected          Rejected
```

### Head Applies on Behalf — Regular Department

```
  Head applies for employee
         │
         ▼
  Head_Approved  ──────────────────►  MD  ──►  HR  ──►  Approved
  (auto, skip Head stage)
```

### Head Applies on Behalf — Support Staff Department

```
  Head applies for support staff
         │
         ▼
  MD_Approved  ────────────────────────────►  HR  ──►  Approved
  (auto, skip Head + MD stages)
```

> The **Support Staff flag** on a department is what drives this fast-track.

---

## Slide 6 — Rejoining Date System

A key feature that tracks whether an employee returned earlier or later than planned.

### How It Works

```
Head applies leave:
  expected_from = 1 June
  expected_to   = 5 June   ──► days = 5

Rejoining date (set by Head):
  rejoined_on = 7 June    ──► actual_days = 7  (+2 extended)
  rejoined_on = 5 June    ──► actual_days = 5  (same as applied)
  rejoined_on = 3 June    ──► actual_days = 3  (−2 early return)
```

### Formula

```
actual_days = (rejoined_on − expected_from).days + 1
```

### When It's Set

1. **At leave creation** — Head can optionally enter rejoining date when applying on behalf.
   Default = `expected_to` (the applied end date).

2. **After leave is recorded** — Head visits `/leave/<pk>/set-rejoining/` at any time
   to update the actual rejoining date. Recalculates automatically.

---

## Slide 7 — HR Portal Features

The HR account has access to everything.

### Dashboard at a Glance
- Total Employees count
- Pending Approvals count
- Approved Leaves count

### Employee Management
| Action | Route |
|---|---|
| Add employee | `/employee/add/` |
| Edit employee | `/employee/<pk>/edit/` |
| Bulk CSV upload | `/employee-upload/` |
| View profile | `/employee/<pk>/` |

### Settings Panel
| Setting | What it manages |
|---|---|
| Departments | Name + Support Staff toggle |
| Leave Types | Annual, Sick, Emergency, etc. |
| MD Accounts | Create/delete MD system logins |
| MOL Records | Ministry of Labor documents |

---

## Slide 8 — MD Portal Features

MD is the **Managing Director** — a system-level account.

**Created by:** HR from Settings → MD Accounts
**Has:** Django User account + Role(MD)
**Does not have:** Employee record

### What MD Sees

- All employees (read-only — cannot add or edit)
- Full leave history (all departments)
- Pending approvals (leaves waiting for MD action — status = `Head_Approved`)
- Org chart
- MOL records (can add/edit)
- Notifications

### MD Approval Action

```
/leaves/pending/
    Shows: all Head_Approved leaves
    Action: Approve → MD_Approved (goes to HR)
            Reject  → Rejected (with reason)
```

---

## Slide 9 — Head Portal Features

Each Head is linked to exactly **one department**.

### Department Dashboard

| Section | What it shows |
|---|---|
| Stats bar | Total employees, pending approvals |
| Employee table | All dept staff with leave counts + action buttons |
| Pending table | Leaves waiting for Head review (inline, no redirect needed) |
| Recent approved | Last few approved leaves |

### Head Actions Per Employee

```
[View Leaves]  [View Profile]  [Apply Leave]
```

### Head Leave View (`/leaves/history/`)

- Dept-scoped — only sees their department's leave records
- Search by name or employee ID
- Filter by leave type
- **Rejoining / Actual Days column** per record
- **Set Rejoining** button on each row

---

## Slide 10 — Notification System

Auto-triggered on every leave status change.

```python
# Auto-notification when Head approves
Notification.objects.create(
    recipient=leave.employee.user,
    message=f"Your leave from {from} to {to} has been approved by Head."
)
```

### Notification Flow

```
Leave status change (approve / reject)
        │
        ▼
  Notification created for employee
        │
        ▼
  Bell icon in nav shows unread count
        │
        ▼
  Employee reads → mark as read
```

---

## Slide 11 — Key Technical Decisions

### 1. Role-Based Template Variable Collision Fix

**Problem:** `base.html` uses `{% with user_role=... %}` which shadowed context variables of the same name in child templates.

**Fix:** Any view context variable that refers to a role object is now named `approver_role` (not `user_role`) to avoid the collision.

### 2. Manager Role Removed

The original 4-stage flow (Pending → Manager_Approved → Head_Approved → MD_Approved → Approved) was simplified to **3 stages** by removing the Manager role entirely. This reduces complexity and maps better to the actual org structure.

### 3. Salary Model Removed

A separate `Salary` model was removed. Salary is now a single `emp_salary` (FloatField) on the Employee model. A full salary history feature can be added later without breaking existing data.

### 4. Support Staff Fast-Track

Rather than hard-coding employee categories, the `is_support_staff` flag on `Department` drives the approval shortcut. This means any department can be designated support staff from Settings without code changes.

---

## Slide 12 — Migration History Summary

| Migration | Change |
|---|---|
| `0001–0010` | Initial models: Employee, Department, Leave, Role |
| `0011–0015` | Added LeaveType, MOL, Notification models |
| `0016–0018` | Added `rejoined_on`, `actual_days` to Leave |
| `0019–0020` | Added head/MD approval tracking fields |
| `0021` | **Removed Salary model; removed Manager from choices** |

---

## Slide 13 — What's Working End-to-End

- [x] Login / logout / forgot password (DOB verification)
- [x] HR: full CRUD on employees, departments, leave types
- [x] HR: bulk employee upload
- [x] HR: create and delete MD system accounts
- [x] HR: final leave approval (MD_Approved → Approved)
- [x] MD: view employees, approve Head_Approved leaves
- [x] Head: department dashboard with inline pending leaves
- [x] Head: approve/reject Pending leaves from their dept
- [x] Head: apply leave on behalf of any dept employee (auto-approves Head stage)
- [x] Head: support staff fast-track (auto-approves Head + MD)
- [x] Head: set / update rejoining date with automatic recalculation
- [x] Leave history with search + filter (role-scoped)
- [x] Org chart
- [x] Notifications (auto-created on status change)
- [x] MOL records management
- [x] Change password

---

## Slide 14 — Future Roadmap

| Feature | Status |
|---|---|
| Full salary history with month-wise records | Planned |
| Employee self-service leave application | Partial (views exist) |
| Leave balance / leave quota per employee | Not started |
| Email notifications on leave events | Not started |
| PostgreSQL production database | Configuration only |
| Attendance tracking | Not started |
| PDF export of leave records | Not started |
| API layer (Django REST Framework) | Not started |

---

*HR Module · Django · Built June 2026*
