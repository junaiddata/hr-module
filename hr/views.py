from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import EmployeeForm
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django_countries import countries
from django.http import JsonResponse
from django.utils import timezone

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            try:
                user_role = request.user.role.role
            except Exception:
                return render(request, 'hr_de/unauthorized.html', status=403)
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            return render(request, 'hr_de/unauthorized.html', status=403)
        return wrapper_func
    return decorator


def _is_hr_department(dept):
    """The 'HR' department is special: its head gets full HR access, so we store
    their Role as 'HR' (scoped to the HR dept) instead of 'Head'."""
    return bool(dept) and (dept.name or '').strip().upper() == 'HR'


def _head_role_for(dept):
    """Role value to assign when making someone head of `dept`."""
    return 'HR' if _is_hr_department(dept) else 'Head'


@login_required
def employee_list(request):
    query = request.GET.get('q')
    status_filter = request.GET.get('employee_status')
    active_filter = request.GET.get('is_active')

    employees = Employee.objects.all()

    # Restrict employees for department head
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        dept = request.user.role.department
        employees = employees.filter(department=dept) if dept else employees.none()

    if query:
        employees = employees.filter(
            Q(emp_name__icontains=query) |
            Q(emp_id__icontains=query)
        )

    if status_filter:
        employees = employees.filter(employee_status=status_filter)

    # Active/inactive filter
    if active_filter:
        employees = employees.filter(is_active=(active_filter == 'true'))

    # Pass status choices to template
    status_choices = Employee.EMPLOYEE_STATUS_CHOICES
    active_count = employees.filter(is_active=True).count()
    inactive_count = employees.filter(is_active=False).count()

    # Role-based template rendering for employee list
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        template_name = 'hr_de/employee_list_head.html'
    else:
        template_name = 'hr_de/employee_list.html'

    return render(request, template_name, {
        'employees': employees,
        'status_choices': status_choices,
        'query': query,
        'selected_status': status_filter,
        'selected_active': active_filter,
        'active_count': active_count,
        'inactive_count': inactive_count,
    })

@login_required
def employee_create(request):
    # Inline role check — Head users cannot create employees
    try:
        user_role = request.user.role.role
    except Exception:
        user_role = None

    if user_role not in ['HR']:
        return render(request, 'hr_de/unauthorized.html', status=403)

    if request.method == 'POST':
        data = request.POST
        files = request.FILES

        # Helper function to handle empty dates
        def parse_date(date_str):
            return date_str if date_str else None


        # Get the Mol instance if mol ID was provided
        mol_id = data.get('mol')
        mol_instance = None
        is_active = data.get('is_active') == 'on'
        if mol_id:
            try:
                mol_instance = Mol.objects.get(pk=mol_id)
            except Mol.DoesNotExist:
                pass

        dept_obj = Department.objects.filter(pk=data.get('department')).first()
        employee = Employee.objects.create(
            emp_name=data.get('emp_name'),
            emp_id=data.get('emp_id'),
            photo=files.get('photo'),
            dob=parse_date(data.get('dob')),
            gender=data.get('gender', 'M'),
            nationality=data.get('nationality', 'Indian'),
            contact_number=data.get('contact_number'),
            department=dept_obj,
            designation=data.get('designation'),
            mol=mol_instance,
            joining_date=parse_date(data.get('joining_date')),
            emp_salary= data.get('emp_salary') or None,
            job_location=data.get('job_location'),
            employee_status=data.get('employee_status', 'Active'),
            is_active=is_active,

            passport=files.get('passport'),
            visa=files.get('visa'),
            labour_card=files.get('labour_card'),
            eid=files.get('eid'),
            insurance=files.get('insurance'),
            driving_license=files.get('driving_license'),

            passport_status=data.get('passport_status', 'With company'),
            passport_number=data.get('passport_number'),
            eid_number=data.get('eid_number'),
            labour_card_number=data.get('labour_card_number'),
            insurance_number=data.get('insurance_number'),
            driving_license_number=data.get('driving_license_number'),

            visa_expiry=parse_date(data.get('visa_expiry')),
            passport_expiry=parse_date(data.get('passport_expiry')),
            labour_card_expiry=parse_date(data.get('labour_card_expiry')),
            eid_expiry=parse_date(data.get('eid_expiry')),
            insurance_expiry=parse_date(data.get('insurance_expiry')),
            driving_license_expiry=parse_date(data.get('driving_license_expiry')),
        )

        # Save salary structure if any component is provided
        def _float(key):
            try:
                return float(data.get(key, 0) or 0)
            except ValueError:
                return 0.0

        basic     = _float('basic')
        hra       = _float('hra')
        transport = _float('transport')
        others    = _float('others')
        if any([basic, hra, transport, others]):
            SalaryStructure.objects.create(
                employee=employee,
                basic=basic,
                hra=hra,
                transport=transport,
                others=others,
                updated_by=request.user,
            )

        # Create login account if username provided
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        if username and password:
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' is already taken. Employee created without login account.")
            else:
                new_user = User.objects.create_user(username=username, password=password, first_name=data.get('emp_name', ''))
                employee.user = new_user
                employee.save()

                # Make department head if checked (head of the HR dept becomes full HR)
                if data.get('make_head') == 'on' and dept_obj:
                    Role.objects.update_or_create(
                        user=new_user,
                        defaults={'role': _head_role_for(dept_obj), 'department': dept_obj}
                    )

        return redirect('employee_list')

    return render(request, 'hr_de/employee_form_raw.html', {
        'mols': Mol.objects.all(),
        'countries': countries,
        'departments': Department.objects.all().order_by('name'),
    })


@login_required
def employee_edit(request, pk):
    try:
        _edit_role = request.user.role.role
    except Exception:
        _edit_role = None
    if _edit_role not in ['HR']:
        return render(request, 'hr_de/unauthorized.html', status=403)

    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        data = request.POST
        files = request.FILES

        is_active = data.get('is_active') == 'on'

        # Helper function to handle empty dates
        def parse_date(date_str):
            return date_str if date_str else None

        # Get the Mol instance if mol ID was provided
        mol_id = data.get('mol')
        mol_instance = None
        if mol_id:
            try:
                mol_instance = Mol.objects.get(pk=mol_id)
            except Mol.DoesNotExist:
                pass

        employee.emp_name = data.get('emp_name')
        employee.emp_id = data.get('emp_id')
        employee.dob = parse_date(data.get('dob'))
        employee.gender = data.get('gender')
        employee.nationality = data.get('nationality')
        employee.contact_number = data.get('contact_number')
        dept_obj = Department.objects.filter(pk=data.get('department')).first()
        employee.department = dept_obj
        employee.designation = data.get('designation')
        employee.mol = mol_instance
        employee.joining_date = parse_date(data.get('joining_date'))
        employee.emp_salary = data.get('emp_salary') or None
        employee.job_location = data.get('job_location')
        employee.employee_status = data.get('employee_status')
        employee.is_active = is_active

        employee.passport_status = data.get('passport_status')
        employee.passport_number = data.get('passport_number')
        employee.eid_number = data.get('eid_number')
        employee.labour_card_number = data.get('labour_card_number')
        employee.insurance_number = data.get('insurance_number')
        employee.driving_license_number = data.get('driving_license_number')

        employee.visa_expiry = parse_date(data.get('visa_expiry'))
        employee.passport_expiry = parse_date(data.get('passport_expiry'))
        employee.labour_card_expiry = parse_date(data.get('labour_card_expiry'))
        employee.eid_expiry = parse_date(data.get('eid_expiry'))
        employee.insurance_expiry = parse_date(data.get('insurance_expiry'))
        employee.driving_license_expiry = parse_date(data.get('driving_license_expiry'))

        # Handle file uploads
        if files.get('photo'):
            employee.photo = files.get('photo')
        if files.get('passport'):
            employee.passport = files.get('passport')
        if files.get('visa'):
            employee.visa = files.get('visa')
        if files.get('labour_card'):
            employee.labour_card = files.get('labour_card')
        if files.get('eid'):
            employee.eid = files.get('eid')
        if files.get('insurance'):
            employee.insurance = files.get('insurance')
        if files.get('driving_license'):
            employee.driving_license = files.get('driving_license')

        # Create/update login account
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        make_head = data.get('make_head') == 'on'

        if username:
            if employee.user:
                # Update existing user
                emp_user = employee.user
                if emp_user.username != username:
                    if not User.objects.filter(username=username).exclude(pk=emp_user.pk).exists():
                        emp_user.username = username
                if password:
                    emp_user.set_password(password)
                emp_user.save()
            else:
                if User.objects.filter(username=username).exists():
                    messages.error(request, f"Username '{username}' already taken.")
                else:
                    emp_user = User.objects.create_user(username=username, password=password or 'changeme123', first_name=employee.emp_name)
                    employee.user = emp_user

        employee.save()

        # Update salary structure if any component supplied
        def _float_edit(key):
            try:
                return float(data.get(key, 0) or 0)
            except ValueError:
                return 0.0

        basic     = _float_edit('basic')
        hra       = _float_edit('hra')
        transport = _float_edit('transport')
        others    = _float_edit('others')
        if any([basic, hra, transport, others]):
            SalaryStructure.objects.update_or_create(
                employee=employee,
                defaults={
                    'basic': basic, 'hra': hra,
                    'transport': transport, 'others': others,
                    'updated_by': request.user,
                }
            )

        # Handle head promotion/demotion (head of the HR dept becomes full HR)
        if employee.user:
            emp_user = employee.user
            if make_head and dept_obj:
                Role.objects.update_or_create(
                    user=emp_user,
                    defaults={'role': _head_role_for(dept_obj), 'department': dept_obj}
                )
            elif not make_head:
                # Remove the department-head role if unchecked. Only touches roles
                # scoped to a department, so company-level HR (dept=None) is safe.
                Role.objects.filter(
                    user=emp_user, role__in=['Head', 'HR'], department__isnull=False
                ).delete()

        return redirect('employee_list')

    # Pre-check the "Make Department Head" box for anyone who heads a department
    # (regular heads use role='Head'; the HR-dept head uses role='HR', dept set).
    is_head = False
    if employee.user:
        is_head = Role.objects.filter(
            user=employee.user, role__in=['Head', 'HR'], department__isnull=False
        ).exists()

    return render(request, 'hr_de/employee_form_raw.html', {
        'employee': employee,
        'mols': Mol.objects.all(),
        'countries': countries,
        'departments': Department.objects.all().order_by('name'),
        'is_head': is_head,
    })



@login_required
def employee_detail(request, pk):
    from datetime import date

    employee = get_object_or_404(Employee, pk=pk)

    try:
        viewer_role = request.user.role.role
    except Exception:
        viewer_role = None
    is_own = bool(employee.user_id) and employee.user_id == request.user.id

    # Self-service employees (no HR/MD/Head role) may only view their own profile
    if viewer_role not in ('HR', 'MD', 'Head') and not is_own:
        return render(request, 'hr_de/unauthorized.html', status=403)

    today = date.today()

    def _years_since(d):
        """Whole years between date d and today (age / tenure)."""
        if not d:
            return None
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    def _expiry(d):
        """Return (status, days_left) for a document expiry date.
        status: expired / critical (<=30d) / warning (<=90d) / valid / none."""
        if not d:
            return ('none', None)
        days = (d - today).days
        if days < 0:
            return ('expired', days)
        if days <= 30:
            return ('critical', days)
        if days <= 90:
            return ('warning', days)
        return ('valid', days)

    # Unified document list: label, id number, expiry date, uploaded file, status
    doc_specs = [
        ('Passport',        employee.passport_number,        employee.passport_expiry,        employee.passport),
        ('Visa',            None,                            employee.visa_expiry,            employee.visa),
        ('Labour Card',     employee.labour_card_number,     employee.labour_card_expiry,     employee.labour_card),
        ('Emirates ID',     employee.eid_number,             employee.eid_expiry,             employee.eid),
        ('Insurance',       employee.insurance_number,       employee.insurance_expiry,       employee.insurance),
        ('Driving License', employee.driving_license_number, employee.driving_license_expiry, employee.driving_license),
    ]
    documents = []
    expiry_alerts = 0
    for label, number, expiry, file in doc_specs:
        status, days = _expiry(expiry)
        if status in ('expired', 'critical', 'warning'):
            expiry_alerts += 1
        documents.append({
            'label': label,
            'number': number,
            'expiry': expiry,
            'file': file,
            'status': status,
            'days': days,
            'abs_days': abs(days) if days is not None else None,
        })

    return render(request, 'hr_de/employee_detail.html', {
        'employee': employee,
        'documents': documents,
        'expiry_alerts': expiry_alerts,
        'age': _years_since(employee.dob),
        'tenure': _years_since(employee.joining_date),
        'is_own': is_own,
    })


@login_required
@require_POST
def upload_my_photo(request):
    """Employee updates ONLY their own profile photo — no other fields."""
    try:
        employee = request.user.employee
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    photo = request.FILES.get('photo')
    if not photo:
        messages.error(request, 'Please choose an image file to upload.')
        return redirect('employee_detail', pk=employee.pk)

    content_type = getattr(photo, 'content_type', '') or ''
    if not content_type.startswith('image/'):
        messages.error(request, 'Only image files (JPG, PNG, WEBP) are allowed.')
        return redirect('employee_detail', pk=employee.pk)

    employee.photo = photo
    employee.save(update_fields=['photo', 'updated_at'])
    messages.success(request, 'Your profile photo has been updated.')
    return redirect('employee_detail', pk=employee.pk)


@login_required
def my_profile(request):
    """Send any logged-in user to their own profile page."""
    try:
        employee = request.user.employee
    except Exception:
        messages.error(request, 'Your account is not linked to an employee record.')
        return redirect('home')
    return redirect('employee_detail', pk=employee.pk)


@login_required
def birthdays(request):
    """HR view of employee birthdays — defaults to this + next month, or a single
    month picked via ?month=1-12. Supports ?export=pdf. Active employees only."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    from datetime import date
    import calendar
    from .whatsapp import whatsapp_configured

    today = date.today()

    # Employees already wished this year (to show "Sent" state on today's cards)
    wished_ids = set(
        BirthdayWish.objects.filter(year=today.year, status='sent')
        .values_list('employee_id', flat=True)
    )

    def _occurrence(dob, year):
        try:
            return date(year, dob.month, dob.day)
        except ValueError:                   # Feb 29 in a non-leap year
            return date(year, dob.month, 28)

    def _row(e, bday):
        return {
            'employee':   e,
            'day':        e.dob.day,
            'bday':       bday,
            'turning':    bday.year - e.dob.year,
            'days_until': (bday - today).days,
            'is_today':   e.dob.month == today.month and e.dob.day == today.day,
            'wished':     e.pk in wished_ids,
        }

    def build(month, year):
        qs = Employee.objects.filter(is_active=True, dob__month=month).select_related('department')
        rows = [_row(e, _occurrence(e.dob, year)) for e in qs]
        rows.sort(key=lambda r: r['day'])
        return rows

    # ── Single month picker (?month=1-12) ───────────────────────────
    try:
        sel_month = int(request.GET.get('month') or 0)
    except (ValueError, TypeError):
        sel_month = 0
    month_mode = 1 <= sel_month <= 12

    if month_mode:
        # Use the upcoming occurrence of that month for "turns X"
        year = today.year if sel_month >= today.month else today.year + 1
        rows = build(sel_month, year)
        sections = [(f"{calendar.month_name[sel_month]} {year}", rows)]
        total = len(rows)
    else:
        # ── Default: this month + next month ────────────────────────
        this_month = today.month
        next_month = 1 if this_month == 12 else this_month + 1
        this_year  = today.year
        next_year  = this_year + 1 if next_month == 1 else this_year
        this_rows = build(this_month, this_year)
        next_rows = build(next_month, next_year)
        sections = [
            (f"{calendar.month_name[this_month]} (This Month)", this_rows),
            (f"{calendar.month_name[next_month]} (Next Month)", next_rows),
        ]
        total = len(this_rows) + len(next_rows)

    if request.GET.get('export') == 'pdf':
        subtitle = sections[0][0] if month_mode else 'This month and next month'
        return _birthdays_pdf(sections, today, subtitle)

    # Month dropdown options
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]

    return render(request, 'hr_de/birthdays.html', {
        'sections':      sections,
        'total':         total,
        'today':         today,
        'month_mode':    month_mode,
        'selected_month': sel_month if month_mode else 0,
        'months':        months,
        'whatsapp_ready': whatsapp_configured(),
    })


@login_required
def birthday_wish_send(request):
    """AJAX: HR sends a WhatsApp birthday wish to one employee."""
    if not _hr_only(request):
        return JsonResponse({'ok': False, 'error': 'Not authorized.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    from .whatsapp import send_birthday_wish, whatsapp_configured
    import json as _json
    try:
        data = _json.loads(request.body or '{}')
    except ValueError:
        data = {}
    emp_pk = data.get('employee_pk') or request.POST.get('employee_pk')

    emp = Employee.objects.filter(pk=emp_pk, is_active=True).first()
    if not emp:
        return JsonResponse({'ok': False, 'error': 'Employee not found.'}, status=404)
    if not whatsapp_configured():
        return JsonResponse({
            'ok': False,
            'error': 'WhatsApp is not configured yet — add the token and phone number id in settings.',
        }, status=400)

    ok, info = send_birthday_wish(emp, sent_by=request.user)
    if ok:
        return JsonResponse({'ok': True, 'message': f'Birthday wish sent to {emp.emp_name}.'})
    return JsonResponse({'ok': False, 'error': info}, status=400)


@login_required
def birthday_wish_log(request):
    """HR view of the WhatsApp birthday-wish send history (sent + failed)."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    from .whatsapp import whatsapp_configured

    base = (BirthdayWish.objects
            .select_related('employee', 'employee__department', 'sent_by'))

    # Counts across everything (for the filter tab badges)
    sent_count = base.filter(status='sent').count()
    failed_count = base.filter(status='failed').count()

    status = request.GET.get('status')
    wishes = base.filter(status=status) if status in ('sent', 'failed') else base

    return render(request, 'hr_de/birthday_wish_log.html', {
        'wishes':        list(wishes),
        'sent_count':    sent_count,
        'failed_count':  failed_count,
        'total':         sent_count + failed_count,
        'status':        status or '',
        'whatsapp_ready': whatsapp_configured(),
    })


def _birthdays_pdf(sections, today, subtitle=''):
    """Render birthday `sections` as a polished, card-style PDF with employee
    photos — mirroring the website design (ReportLab + Pillow)."""
    import io, os
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from PIL import Image as PILImage, ImageDraw, ImageFont

    BRAND = colors.HexColor('#2208cd')
    PINK  = colors.HexColor('#ec4899')
    INK   = colors.HexColor('#0f172a')
    MUTE  = colors.HexColor('#64748b')

    def _avatar(employee, bg=(255, 255, 255), size=120):
        """Circular avatar PNG (photo centre-cropped, or a coloured initial),
        composited onto the row background `bg` so corners stay clean on any
        ReportLab version (no reliance on PNG alpha)."""
        base  = PILImage.new('RGBA', (size, size), (0, 0, 0, 0))
        drawn = False
        if getattr(employee, 'photo', None):
            try:
                path = employee.photo.path
                if os.path.exists(path):
                    ph = PILImage.open(path).convert('RGB')
                    w, h = ph.size
                    m = min(w, h)
                    ph = ph.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m)).resize((size, size))
                    base.paste(ph, (0, 0))
                    drawn = True
            except Exception:
                drawn = False
        if not drawn:
            d = ImageDraw.Draw(base)
            d.ellipse((0, 0, size - 1, size - 1), fill=(34, 8, 205, 255))
            letter = ((employee.emp_name or '?').strip()[:1] or '?').upper()
            font = None
            for fname in ('arialbd.ttf', 'arial.ttf', 'DejaVuSans-Bold.ttf'):
                try:
                    font = ImageFont.truetype(fname, int(size * 0.46)); break
                except Exception:
                    continue
            if font is None:
                font = ImageFont.load_default()
            bb = d.textbbox((0, 0), letter, font=font)
            d.text(((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1]),
                   letter, font=font, fill=(255, 255, 255, 255))
        mask = PILImage.new('L', (size, size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
        # Composite the masked avatar onto the row background → flat RGB, clean edges
        canvas = PILImage.new('RGB', (size, size), bg)
        canvas.paste(base, (0, 0), mask)
        buf = BytesIO(); canvas.save(buf, 'PNG'); buf.seek(0)
        return buf

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm, leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        title='Upcoming Birthdays',
    )
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle('name', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=INK, leading=12)
    role_style = ParagraphStyle('role', parent=styles['Normal'], fontSize=8, textColor=MUTE, leading=10)
    date_style = ParagraphStyle('date', parent=styles['Normal'], fontSize=10, textColor=INK, alignment=2, leading=12)
    turn_style = ParagraphStyle('turn', parent=styles['Normal'], fontSize=8, textColor=MUTE, alignment=2, leading=11)
    hdr_style  = ParagraphStyle('hdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, textColor=colors.white, leading=14)

    # Title band
    elems = []
    band = Table([[Paragraph('Upcoming Birthdays', ParagraphStyle('tt', fontName='Helvetica-Bold', fontSize=17, textColor=colors.white))]],
                 colWidths=[doc.width])
    band.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND),
        ('TOPPADDING', (0, 0), (-1, -1), 12), ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
    ]))
    elems.append(band)
    elems.append(Spacer(1, 5))
    elems.append(Paragraph((subtitle + ' &nbsp;&middot;&nbsp; ' if subtitle else '') + 'Generated on ' + today.strftime('%d %b %Y'),
                           ParagraphStyle('sub', fontSize=9, textColor=MUTE)))
    elems.append(Spacer(1, 12))

    def status_para(r):
        if r['is_today']:
            txt, col = 'Today', PINK
        elif r['days_until'] < 0:
            txt, col = 'Celebrated', MUTE
        elif r['days_until'] <= 7:
            txt, col = ('In %d day%s' % (r['days_until'], '' if r['days_until'] == 1 else 's'), colors.HexColor('#b45309'))
        else:
            txt, col = ('In %d days' % r['days_until'], colors.HexColor('#1d4ed8'))
        return Paragraph('<b>%s</b>' % txt, ParagraphStyle('st', fontSize=8, textColor=col, alignment=2, leading=11))

    def section(title, rows):
        sh = Table([[Paragraph('%s  (%d)' % (title, len(rows)), hdr_style)]], colWidths=[doc.width])
        sh.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PINK),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elems.append(sh)
        elems.append(Spacer(1, 6))
        if not rows:
            elems.append(Paragraph('No birthdays.', role_style))
            elems.append(Spacer(1, 12))
            return
        data = []
        for i, r in enumerate(rows):
            e = r['employee']
            row_bg = (255, 255, 255) if i % 2 == 0 else (253, 242, 248)  # matches ROWBACKGROUNDS
            meta = e.designation or '—'
            if e.department:
                meta += ' &middot; %s' % e.department.name
            name_cell = [Paragraph(e.emp_name, name_style), Paragraph(meta, role_style)]
            date_cell = [
                Paragraph('<font color="#ec4899"><b>%s</b></font> %s' % (r['bday'].strftime('%d'), r['bday'].strftime('%b')), date_style),
                Paragraph('Turns %d' % r['turning'], turn_style),
            ]
            data.append([Image(_avatar(e, bg=row_bg), width=1.0 * cm, height=1.0 * cm), name_cell, date_cell, status_para(r)])
        tbl = Table(data, colWidths=[1.3 * cm, doc.width - 1.3 * cm - 2.6 * cm - 3.0 * cm, 2.6 * cm, 3.0 * cm])
        tbl.setStyle(TableStyle([
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fdf2f8')]),
            ('LINEBELOW', (0, 0), (-1, -1), 0.4, colors.HexColor('#f6d9e8')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elems.append(tbl)
        elems.append(Spacer(1, 14))

    for title, rows in sections:
        section(title, rows)

    doc.build(elems)
    buffer.seek(0)
    resp = HttpResponse(buffer, content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="upcoming_birthdays.pdf"'
    return resp


@login_required
def mol_list(request):
    mols = Mol.objects.all().order_by('mol')
    return render(request, 'hr_de/mols/mol_list.html', {'mols': mols})

@login_required
def mol_add(request):
    if request.method == 'POST':
        def _f(key): return request.POST.get(key, '').strip() or None
        mol = Mol(
            mol=request.POST.get('mol', '').strip(),
            established_year=_f('established_year'),
            trade_license_number=_f('trade_license_number'),
            trade_license_expiry=_f('trade_license_expiry'),
            tenancy_contract_expiry=_f('tenancy_contract_expiry'),
            establishment_card_expiry=_f('establishment_card_expiry'),
        )
        if 'license_document' in request.FILES:
            mol.license_document = request.FILES['license_document']
        if 'tenancy_contract' in request.FILES:
            mol.tenancy_contract = request.FILES['tenancy_contract']
        if 'establishment_card' in request.FILES:
            mol.establishment_card = request.FILES['establishment_card']
        mol.save()
        messages.success(request, f"MOL '{mol.mol}' created successfully.")
        return redirect('mol_list')
    return render(request, 'hr_de/mols/mol_form.html')

@login_required
def mol_edit(request, pk):
    mol = get_object_or_404(Mol, pk=pk)
    if request.method == 'POST':
        def _f(key): return request.POST.get(key, '').strip() or None
        mol.mol                       = request.POST.get('mol', '').strip()
        mol.established_year          = _f('established_year')
        mol.trade_license_number      = _f('trade_license_number')
        mol.trade_license_expiry      = _f('trade_license_expiry')
        mol.tenancy_contract_expiry   = _f('tenancy_contract_expiry')
        mol.establishment_card_expiry = _f('establishment_card_expiry')
        if 'license_document' in request.FILES:
            mol.license_document = request.FILES['license_document']
        if 'tenancy_contract' in request.FILES:
            mol.tenancy_contract = request.FILES['tenancy_contract']
        if 'establishment_card' in request.FILES:
            mol.establishment_card = request.FILES['establishment_card']
        mol.save()
        messages.success(request, f"MOL '{mol.mol}' updated successfully.")
        return redirect('mol_list')
    return render(request, 'hr_de/mols/mol_form.html', {'mol': mol})



@require_POST
def mol_delete(request, pk):
    mol = get_object_or_404(Mol, pk=pk)
    mol.delete()
    return redirect('mol_list')


# ── Department CRUD ──────────────────────────────────────────────────────────

@login_required
def department_list(request):
    all_depts = Department.objects.all().order_by('name')
    # Split out shops/stores into their own section (name starts with SHOP or STORE)
    shops, departments = [], []
    for d in all_depts:
        name = (d.name or '').strip().upper()
        (shops if name.startswith('SHOP') or name.startswith('STORE') else departments).append(d)
    return render(request, 'hr_de/departments/department_list.html', {
        'departments': departments,
        'shops': shops,
    })

@login_required
def department_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_support_staff = request.POST.get('is_support_staff') == 'on'
        if name:
            Department.objects.get_or_create(name=name, defaults={'is_support_staff': is_support_staff})
        return redirect('department_list')
    return render(request, 'hr_de/departments/department_form.html')

@login_required
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        is_support_staff = request.POST.get('is_support_staff') == 'on'
        if name:
            department.name = name
            department.is_support_staff = is_support_staff
            department.save()
        return redirect('department_list')
    return render(request, 'hr_de/departments/department_form.html', {'department': department})

@require_POST
@login_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    department.delete()
    return redirect('department_list')


#############################       LEAVE MANAGEMENT       #############################
def leave_type_list(request):
    leave_types = LeaveType.objects.all()
    return render(request, 'hr_de/leave_type/leave_type_list.html', {'leave_types': leave_types})

def leave_type_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        LeaveType.objects.create(name=name)
        return redirect('leave_type_list')
    return render(request, 'hr_de/leave_type/leave_type_form.html')

def leave_type_edit(request, pk):
    leave_type = get_object_or_404(LeaveType, pk=pk)

    if request.method == 'POST':
        leave_type.name = request.POST.get('name')
        leave_type.save()
        return redirect('leave_type_list')

    return render(request, 'hr_de/leave_type/leave_type_form.html', {'leave_type': leave_type})


def leave_type_delete(request, pk):
    leave_type = get_object_or_404(LeaveType, pk=pk)
    leave_type.delete()
    return redirect('leave_type_list')

@login_required
def add_leave(request):
    employees = Employee.objects.filter(is_active=True)

    # Restrict employees for department head
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        dept = request.user.role.department
        employees = employees.filter(department=dept) if dept else employees.none()

    leave_types = LeaveType.objects.all()

    if request.method == "POST":
        employee_id = request.POST.get("employee")
        leave_type_id = request.POST.get("leave_type")
        expected_from = request.POST.get("expected_from")
        expected_to = request.POST.get("expected_to")
        reported_to = request.POST.get("reported_to")
        reason = request.POST.get("reason")
        leave_application = request.FILES.get("leave_application")  # Get uploaded file

        Leave.objects.create(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            expected_from=expected_from,
            expected_to=expected_to,
            reported_to=reported_to,
            reason=reason,
            leave_application=leave_application,  # Save the file
            status='Pending'
        )
        return redirect('leave_history')

    # Role-based template rendering
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        template_name = 'hr_de/add_leave_head.html'
    else:
        template_name = 'hr_de/add_leave.html'

    return render(request, template_name, {
        'employees': employees,
        'leave_types': leave_types
    })


@login_required
def approve_leave(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    user_role = getattr(request.user, 'role', None)

    if request.method == "POST":
        action = request.POST.get("action")
        rejection_reason = request.POST.get("rejection_reason", "").strip()

        if user_role and user_role.role == 'Head':
            if leave.status != 'Pending':
                messages.error(request, "This leave is no longer pending for Head approval.")
                return redirect('pending_leaves')
            if leave.employee.department != user_role.department:
                return render(request, 'hr_de/unauthorized.html', status=403)
            if action == 'approve':
                leave.status = 'Head_Approved'
                leave.head_approved_by = request.user
                leave.head_approved_at = timezone.now()
            elif action == 'reject':
                leave.status = 'Rejected'
                leave.head_approved_by = request.user
                leave.rejection_reason = rejection_reason

        elif user_role and user_role.role == 'MD':
            if leave.status != 'Head_Approved':
                messages.error(request, "This leave must be approved by the Head first.")
                return redirect('pending_leaves')
            if action == 'approve':
                leave.status = 'MD_Approved'
                leave.md_approved_by = request.user
                leave.md_approved_at = timezone.now()
            elif action == 'reject':
                leave.status = 'Rejected'
                leave.md_approved_by = request.user
                leave.rejection_reason = rejection_reason

        elif user_role and user_role.role == 'HR':
            if leave.status != 'MD_Approved':
                messages.error(request, "This leave must be approved by the MD first.")
                return redirect('pending_leaves')
            if action == 'approve':
                leave.status = 'Approved'
                leave.approved_by = request.user
            elif action == 'reject':
                leave.status = 'Rejected'
                leave.approved_by = request.user
                leave.rejection_reason = rejection_reason

        else:
            return render(request, 'hr_de/unauthorized.html', status=403)

        leave.save()
        return redirect('pending_leaves')

    return render(request, 'hr_de/approve_leave.html', {
        'leave': leave,
        'approver_role': user_role,
    })


@login_required
def pending_leaves(request):
    user_role = getattr(request.user, 'role', None)

    if user_role and user_role.role == 'Head':
        dept = user_role.department
        leaves = Leave.objects.filter(
            status='Pending',
            employee__department=dept
        ).select_related('employee', 'leave_type') if dept else Leave.objects.none()
    elif user_role and user_role.role == 'MD':
        leaves = Leave.objects.filter(
            status='Head_Approved'
        ).select_related('employee', 'leave_type', 'head_approved_by')
    elif user_role and user_role.role == 'HR':
        leaves = Leave.objects.filter(
            status='MD_Approved'
        ).select_related('employee', 'leave_type', 'head_approved_by', 'md_approved_by')
    else:
        leaves = Leave.objects.none()

    return render(request, 'hr_de/pending_leaves.html', {
        'leaves': leaves,
        'user_role': user_role,
    })

from django.db.models import Q

@login_required
def leave_history(request):
    query = request.GET.get('q') or ''
    leave_type_id = request.GET.get('leave_type')
    status_filter = request.GET.get('status')

    leaves = Leave.objects.select_related('employee', 'leave_type')

    # Filter based on role
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        dept = request.user.role.department
        leaves = leaves.filter(employee__department=dept) if dept else leaves.none()

    # Apply search filters
    if query:
        leaves = leaves.filter(
            Q(employee__emp_name__icontains=query) |
            Q(employee__emp_id__icontains=query)
        )

    if leave_type_id:
        leaves = leaves.filter(leave_type_id=leave_type_id)
        
    if status_filter:
        leaves = leaves.filter(status=status_filter)

    leaves = leaves.order_by('-expected_from')
    leave_types = LeaveType.objects.all()

    # Role-based template rendering for leave history
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        template_name = 'hr_de/leave_history_head.html'
    else:
        template_name = 'hr_de/leave_history.html'

    return render(request, template_name, {
        'leaves': leaves,
        'leave_types': leave_types,
        'query': query,
        'selected_type': leave_type_id,
    })

@login_required
def leave_edit(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    employees = Employee.objects.filter(is_active=True)

    # Restrict employees for department head
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        dept = request.user.role.department
        employees = employees.filter(department=dept) if dept else employees.none()

    leave_types = LeaveType.objects.all()

    if request.method == "POST":
        leave.employee_id = request.POST.get("employee")
        leave.leave_type_id = request.POST.get("leave_type")
        leave.expected_from = request.POST.get("expected_from")
        leave.expected_to = request.POST.get("expected_to")
        leave.reported_to = request.POST.get("reported_to")
        leave.actual_from = request.POST.get("actual_from") or None
        leave.actual_to = request.POST.get("actual_to") or None
        leave.rejoined_on = request.POST.get("rejoined_on") or None
        leave.reason = request.POST.get("reason")
  
        # Handle file upload (replace if new one uploaded)
        if request.FILES.get("leave_application"):
            leave.leave_application = request.FILES.get("leave_application")

        leave.save()
        return redirect('leave_history')

    # Role-based template rendering
    if hasattr(request.user, 'role') and request.user.role.role == 'Head':
        template_name = 'hr_de/add_leave_head.html'
    else:
        template_name = 'hr_de/add_leave.html'

    return render(request, template_name, {
        'leave': leave,
        'employees': employees,
        'leave_types': leave_types
    })


def employee_leave_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    leaves = Leave.objects.filter(employee=employee).order_by('-expected_from')
    total_leave_days = sum(
        (leave.actual_to - leave.actual_from).days + 1 for leave in leaves
        if leave.actual_from and leave.actual_to
    )
    total_leaves = Leave.objects.filter(employee=employee).count()
    sick_leaves = leaves.filter(leave_type__name='Sick').count()
    annual_leaves = leaves.filter(leave_type__name='Annual').count()
    return render(request, 'hr_de/employee_leave_detail.html', {
        'employee': employee,
        'leaves': leaves,
        'total_leave_days': total_leave_days,
        'total_leaves': total_leaves,
        'sick_leaves': sick_leaves,
        'annual_leaves': annual_leaves,
    })


@login_required
def home(request):
    from datetime import date
    today = date.today()
    total_employees = Employee.objects.count()
    pending_leaves = Leave.objects.filter(
        status__in=['Pending', 'Head_Approved', 'MD_Approved']
    ).count()
    approved_leaves = Leave.objects.filter(status='Approved').count()
    recent_leaves = Leave.objects.select_related('employee', 'leave_type').order_by('-created_at')[:5]

    # Active employees celebrating a birthday today
    birthdays_today = Employee.objects.filter(
        is_active=True, dob__month=today.month, dob__day=today.day
    ).select_related('department').order_by('emp_name')

    return render(request, 'hr_de/home.html', {
        'total_employees': total_employees,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'recent_leaves': recent_leaves,
        'today': today,
        'birthdays_today': birthdays_today,
    })

@login_required
def employee_home(request):
    user_role = getattr(request.user, 'role', None)
    dept = user_role.department if user_role else None

    from django.db.models import Count, Q as DQ
    employees = Employee.objects.filter(department=dept).annotate(
        total_leaves=Count('leave'),
        pending_leaves=Count('leave', filter=DQ(leave__status='Pending')),
        approved_leaves=Count('leave', filter=DQ(leave__status='Approved')),
        rejected_leaves=Count('leave', filter=DQ(leave__status='Rejected')),
    ).order_by('emp_name') if dept else Employee.objects.none()

    pending_for_head = Leave.objects.filter(
        employee__department=dept, status='Pending'
    ).select_related('employee', 'leave_type').order_by('-created_at') if dept else Leave.objects.none()

    recent_approved = Leave.objects.filter(
        employee__department=dept, status='Approved'
    ).select_related('employee', 'leave_type').order_by('-created_at')[:10] if dept else Leave.objects.none()

    leave_types = LeaveType.objects.all()
    is_support_staff = dept.is_support_staff if dept else False

    return render(request, 'hr_de/employee_home.html', {
        'employees': employees,
        'dept': dept,
        'dept_name': dept.name if dept else '',
        'pending_for_head': pending_for_head,
        'recent_approved': recent_approved,
        'leave_types': leave_types,
        'is_support_staff': is_support_staff,
        'total_employees': employees.count(),
        'total_pending': pending_for_head.count(),
    })

@login_required
def org_chart(request):
    try:
        user_role = request.user.role.role
    except Exception:
        user_role = None
    if user_role not in ['HR', 'Manager', 'MD']:
        return render(request, 'hr_de/unauthorized.html', status=403)

    departments = Department.objects.all().order_by('name')
    chart_data = []
    for dept in departments:
        # The HR dept's head is stored as role='HR' (scoped to the dept); include it.
        head_roles = Role.objects.filter(
            department=dept, role__in=['Head', 'HR']
        ).select_related('user')
        heads = []
        for hr in head_roles:
            try:
                emp = hr.user.employee
            except Exception:
                emp = None
            heads.append({'user': hr.user, 'employee': emp})

        all_employees = Employee.objects.filter(department=dept).select_related('user')
        head_emp_pks = {h['employee'].pk for h in heads if h['employee']}
        regular = [e for e in all_employees if e.pk not in head_emp_pks]

        name = (dept.name or '').strip().upper()
        chart_data.append({
            'department': dept,
            'heads': heads,
            'employees': regular,
            'total': all_employees.count(),
            'is_shop': name.startswith('SHOP') or name.startswith('STORE'),
        })

    # Split shops/stores into their own section
    shop_data = [c for c in chart_data if c['is_shop']]
    chart_data = [c for c in chart_data if not c['is_shop']]

    # Company-level management only (dept=None) — dept-scoped HR heads show under their dept
    top_mgmt = Role.objects.filter(
        role__in=['MD', 'HR'], department__isnull=True
    ).select_related('user')
    return render(request, 'hr_de/org_chart.html', {
        'chart_data': chart_data,
        'shop_data': shop_data,
        'top_mgmt': top_mgmt,
        'can_assign_head': user_role == 'HR',
    })


@login_required
def assign_head(request):
    """AJAX: drag an employee onto a department head zone to promote them."""
    import json
    try:
        caller_role = request.user.role.role
    except Exception:
        caller_role = None
    if caller_role != 'HR':
        return JsonResponse({'ok': False, 'error': 'Permission denied.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required.'}, status=405)

    try:
        data       = json.loads(request.body)
        emp_pk     = int(data['employee_pk'])
        dept_pk    = int(data['department_pk'])
    except (KeyError, ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid payload.'}, status=400)

    employee   = get_object_or_404(Employee, pk=emp_pk)
    department = get_object_or_404(Department, pk=dept_pk)

    if not employee.user:
        return JsonResponse({
            'ok': False,
            'error': f'"{employee.emp_name}" has no login account. '
                     'Assign a username via Edit Employee first.'
        })

    # Assign / update the head role (head of the HR dept becomes full HR)
    role_value = _head_role_for(department)
    Role.objects.update_or_create(
        user=employee.user,
        defaults={'role': role_value, 'department': department}
    )

    # Move employee to the target department if they belong to a different one
    if employee.department_id != dept_pk:
        employee.department = department
        employee.save(update_fields=['department'])

    label = 'HR' if role_value == 'HR' else 'Head'
    return JsonResponse({
        'ok': True,
        'message': f'{employee.emp_name} is now {label} of {department.name}.'
    })


def settings(request):
    return render(request, 'hr_de/settings.html', {})


# ── Employee self-service ────────────────────────────────────────────────────

@login_required
def employee_dashboard(request):
    """Landing dashboard for a regular (self-service) employee — greeting + feature tiles."""
    try:
        employee = request.user.employee
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    leaves        = Leave.objects.filter(employee=employee)
    advances      = AdvanceSalary.objects.filter(employee=employee)
    passport_reqs = PassportRequest.objects.filter(employee=employee)

    stats = {
        'pending_leaves':   leaves.filter(status__in=['Pending', 'Head_Approved', 'MD_Approved']).count(),
        'approved_leaves':  leaves.filter(status='Approved').count(),
        'pending_advances': advances.filter(status__in=['Pending', 'Head_Approved']).count(),
        'active_advances':  advances.filter(status='Approved').count(),
        'pending_passport': passport_reqs.filter(status='Pending').count(),
        'outstanding_passport': passport_reqs.filter(status='Approved').count(),
    }

    from datetime import date
    _today = date.today()
    is_birthday = bool(employee.dob) and (employee.dob.month, employee.dob.day) == (_today.month, _today.day)

    return render(request, 'hr_de/employee_dashboard.html', {
        'employee': employee,
        'stats': stats,
        'is_birthday': is_birthday,
    })


@login_required
def my_leaves(request):
    """Personal leave dashboard for regular employees."""
    try:
        employee = request.user.employee
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    leaves = Leave.objects.filter(employee=employee).select_related('leave_type').order_by('-created_at')
    leave_types = LeaveType.objects.all()

    total  = leaves.count()
    pending  = leaves.filter(status='Pending').count()
    approved = leaves.filter(status='Approved').count()
    rejected = leaves.filter(status='Rejected').count()

    return render(request, 'hr_de/my_leaves.html', {
        'employee': employee,
        'leaves': leaves,
        'leave_types': leave_types,
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
    })


@login_required
def submit_my_leave(request):
    """Employee submits their own leave request."""
    try:
        employee = request.user.employee
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    leave_types = LeaveType.objects.all()

    if request.method == 'POST':
        expected_from = request.POST.get('expected_from')
        expected_to   = request.POST.get('expected_to')
        if expected_from and expected_to:
            from datetime import date
            days = (
                date.fromisoformat(expected_to) - date.fromisoformat(expected_from)
            ).days + 1
        else:
            days = 0

        Leave.objects.create(
            employee=employee,
            leave_type_id=request.POST.get('leave_type'),
            expected_from=expected_from,
            expected_to=expected_to,
            reported_to=request.POST.get('reported_to', ''),
            reason=request.POST.get('reason', ''),
            days=days,
            leave_application=request.FILES.get('leave_application'),
            status='Pending',
        )
        messages.success(request, "Leave request submitted successfully.")
        return redirect('my_leaves')

    return render(request, 'hr_de/submit_leave.html', {
        'employee': employee,
        'leave_types': leave_types,
    })


# ── Head: apply leave on behalf of any employee in their department ──────────

@login_required
def apply_leave_behalf(request, emp_pk):
    """Head applies leave for any employee under their department.
    Auto-approves the Head stage; support-staff depts also skip MD."""
    try:
        user_role = request.user.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    if user_role.role != 'Head':
        return render(request, 'hr_de/unauthorized.html', status=403)

    dept = user_role.department
    employee = get_object_or_404(Employee, pk=emp_pk, department=dept)
    leave_types = LeaveType.objects.all()

    if request.method == 'POST':
        from datetime import date as _date
        expected_from_str = request.POST.get('expected_from')
        expected_to_str   = request.POST.get('expected_to')
        rejoined_on_str   = request.POST.get('rejoined_on', '').strip()

        expected_from = _date.fromisoformat(expected_from_str) if expected_from_str else None
        expected_to   = _date.fromisoformat(expected_to_str)   if expected_to_str   else None

        if expected_from and expected_to:
            days = (expected_to - expected_from).days + 1
        else:
            days = 0

        # Rejoining date defaults to expected_to; actual_days recalculated from it
        if rejoined_on_str:
            rejoined_on  = _date.fromisoformat(rejoined_on_str)
            actual_days  = (rejoined_on - expected_from).days + 1 if expected_from else days
        else:
            rejoined_on  = expected_to
            actual_days  = days

        # Head already approved — determine next stage based on dept type
        is_support = dept.is_support_staff if dept else False
        if is_support:
            # Support staff: skip Head + MD → goes straight to HR
            status = 'MD_Approved'
        else:
            # Regular dept: skip Head → goes to MD next
            status = 'Head_Approved'

        Leave.objects.create(
            employee=employee,
            leave_type_id=request.POST.get('leave_type'),
            expected_from=expected_from,
            expected_to=expected_to,
            reported_to=request.POST.get('reported_to', f"{request.user.get_full_name() or request.user.username} (Head)"),
            reason=request.POST.get('reason', ''),
            days=days,
            actual_days=actual_days,
            rejoined_on=rejoined_on,
            leave_application=request.FILES.get('leave_application'),
            status=status,
            head_approved_by=request.user,
            head_approved_at=timezone.now(),
        )
        messages.success(request, f"Leave applied for {employee.emp_name} and auto-approved at Head stage.")
        return redirect('employee_home')

    return render(request, 'hr_de/apply_leave_behalf.html', {
        'employee': employee,
        'leave_types': leave_types,
        'dept': dept,
    })


# ── Head: update rejoining date on a dept employee's leave ───────────────────

@login_required
def set_rejoining_date(request, leave_pk):
    """Head sets/updates the actual rejoining date for a leave in their dept.
    Recalculates actual_days = (rejoined_on - expected_from).days + 1."""
    try:
        user_role = request.user.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    if user_role.role != 'Head':
        return render(request, 'hr_de/unauthorized.html', status=403)

    leave = get_object_or_404(Leave, pk=leave_pk, employee__department=user_role.department)

    if request.method == 'POST':
        from datetime import date as _date
        rejoined_str = request.POST.get('rejoined_on', '').strip()
        if rejoined_str and leave.expected_from:
            rejoined_on = _date.fromisoformat(rejoined_str)
            actual_days = (rejoined_on - leave.expected_from).days + 1
            leave.rejoined_on = rejoined_on
            leave.actual_days = actual_days
            leave.save()
            messages.success(request, f"Rejoining date updated for {leave.employee.emp_name}. Actual days: {actual_days}.")
        else:
            messages.error(request, "Invalid rejoining date.")
        return redirect('leave_history')

    return render(request, 'hr_de/set_rejoining_date.html', {'leave': leave})


# ── HR: set / edit salary structure for an employee ─────────────────────────

@login_required
def salary_structure(request, emp_pk):
    try:
        user_role = request.user.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)
    if user_role.role != 'HR':
        return render(request, 'hr_de/unauthorized.html', status=403)

    employee = get_object_or_404(Employee, pk=emp_pk)

    # Get or create the salary structure record
    structure, _ = SalaryStructure.objects.get_or_create(employee=employee)

    if request.method == 'POST':
        def _float(key):
            try:
                return float(request.POST.get(key, 0) or 0)
            except ValueError:
                return 0.0

        structure.basic     = _float('basic')
        structure.hra       = _float('hra')
        structure.transport = _float('transport')
        structure.others    = _float('others')
        structure.updated_by = request.user
        structure.save()
        messages.success(request, f"Salary structure updated for {employee.emp_name}.")
        return redirect('employee_detail', pk=emp_pk)

    return render(request, 'hr_de/salary_structure.html', {
        'employee': employee,
        'structure': structure,
    })


# ── PAYROLL VIEWS ────────────────────────────────────────────────────────────

def _hr_only(request):
    try:
        return request.user.role.role == 'HR'
    except Exception:
        return False


@login_required
def payroll_list(request):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    runs = PayrollRun.objects.prefetch_related('entries').all()
    return render(request, 'hr_de/payroll/payroll_list.html', {
        'runs': runs,
        'draft_count': runs.filter(status='Draft').count(),
        'confirmed_count': runs.filter(status='Confirmed').count(),
    })


@login_required
def payroll_create(request):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    if request.method == 'POST':
        month = int(request.POST.get('month', 0))
        year  = int(request.POST.get('year',  0))
        notes = request.POST.get('notes', '')

        if PayrollRun.objects.filter(month=month, year=year).exists():
            messages.error(request, f"Payroll for {month}/{year} already exists.")
            return redirect('payroll_list')

        # Attendance must be complete for the month before payroll can run
        gaps = _attendance_incomplete(year, month)
        if gaps:
            total_missing = sum(m for _, m in gaps)
            preview = ', '.join(
                f"{e.emp_name} ({m} day{'s' if m != 1 else ''})" for e, m in gaps[:6]
            )
            more = '' if len(gaps) <= 6 else f", +{len(gaps) - 6} more"
            month_name = dict(PayrollRun.MONTH_CHOICES).get(month, month)
            messages.error(
                request,
                f"Cannot run payroll — attendance for {month_name} {year} is incomplete. "
                f"{len(gaps)} employee(s) have {total_missing} unfilled day(s): {preview}{more}. "
                f"Please complete the Attendance Sheet for every employee first."
            )
            return redirect('payroll_create')

        run = PayrollRun.objects.create(
            month=month, year=year, notes=notes, created_by=request.user
        )

        # Auto-populate one entry per active employee that has a salary structure
        employees = Employee.objects.filter(is_active=True).select_related('salary_structure')
        created = 0
        for emp in employees:
            try:
                s = emp.salary_structure
            except Exception:
                s = None

            # Check for an active approved advance salary with remaining balance
            advance_ded, advance_obj = _pick_active_advance(emp)

            gross = s.total if s else 0
            absent, half, att_ded = _attendance_deduction_for(emp, year, month, gross)
            entry = PayrollEntry(
                payroll_run=run,
                employee=emp,
                basic=s.basic if s else 0,
                hra=s.hra if s else 0,
                transport=s.transport if s else 0,
                others=s.others if s else 0,
                advance_deduction=advance_ded,
                advance_salary=advance_obj,
                absent_days=absent,
                half_days=half,
                attendance_deduction=att_ded,
            )
            entry.compute_and_save()
            created += 1

        messages.success(request, f"Payroll run created with {created} employee entries.")
        return redirect('payroll_detail', pk=run.pk)

    from datetime import date
    today = date.today()
    return render(request, 'hr_de/payroll/payroll_create.html', {
        'current_month': today.month,
        'current_year':  today.year,
        'month_choices': PayrollRun.MONTH_CHOICES,
    })


def _attendance_deduction_for(employee, year, month, gross):
    """Return (absent_days, half_days, deduction) for an employee in a month.

    Per-day rate = gross salary / total days in the month. Each absent day deducts
    one full day; each half day deducts half a day.
    """
    import calendar
    import datetime as dt
    num_days = calendar.monthrange(year, month)[1]
    first = dt.date(year, month, 1)
    last  = dt.date(year, month, num_days)
    qs = Attendance.objects.filter(employee=employee, date__range=(first, last))
    absent = qs.filter(status='absent').count()
    half   = qs.filter(status='half_day').count()
    per_day = (gross / num_days) if (num_days and gross) else 0
    deduction = round(per_day * absent + (per_day / 2.0) * half, 2)
    return absent, half, deduction


def _attendance_incomplete(year, month):
    """Return [(employee, missing_days), ...] for active employees with blank
    attendance days that must be filled before payroll can run.

    A day counts as filled if it has an Attendance record, is covered by an
    approved leave, or is a Sunday (auto week-off). Days before an employee's
    joining date and days still in the future are not required.
    """
    import calendar
    import datetime as dt
    today    = timezone.localdate()
    num_days = calendar.monthrange(year, month)[1]
    first    = dt.date(year, month, 1)
    last     = dt.date(year, month, num_days)
    cutoff   = min(last, today)

    employees = list(Employee.objects.filter(is_active=True))
    emp_ids   = [e.id for e in employees]

    have = set()
    for eid, d in Attendance.objects.filter(
        employee_id__in=emp_ids, date__range=(first, last)
    ).values_list('employee_id', 'date'):
        have.add((eid, d.day))

    leave_days = set()
    for lv in Leave.objects.filter(employee_id__in=emp_ids, status='Approved'):
        f = lv.actual_from or lv.expected_from
        t = lv.actual_to or lv.expected_to
        if not f or not t:
            continue
        cur = max(f, first)
        end = min(t, last)
        while cur <= end:
            leave_days.add((lv.employee_id, cur.day))
            cur += dt.timedelta(days=1)

    gaps = []
    for emp in employees:
        missing = 0
        for d in range(1, num_days + 1):
            dobj = dt.date(year, month, d)
            if dobj > cutoff:
                continue                              # future day — not yet required
            if emp.joining_date and dobj < emp.joining_date:
                continue                              # before joining — excused
            if dobj.weekday() == 6:
                continue                              # Sunday auto week-off
            if (emp.id, d) in have or (emp.id, d) in leave_days:
                continue
            missing += 1
        if missing:
            gaps.append((emp, missing))
    return gaps


def _sync_attendance_deductions(run):
    """Refresh attendance deductions on a DRAFT run from current attendance records."""
    if run.status != 'Draft':
        return
    for entry in run.entries.select_related('employee'):
        absent, half, ded = _attendance_deduction_for(
            entry.employee, run.year, run.month, entry.gross_salary or 0
        )
        if (entry.absent_days != absent or entry.half_days != half
                or round(entry.attendance_deduction, 2) != round(ded, 2)):
            entry.absent_days          = absent
            entry.half_days            = half
            entry.attendance_deduction = ded
            entry.compute_and_save()


def _pick_active_advance(employee):
    """Return (deduction_amount, advance_obj) for the employee's oldest active advance."""
    for adv in employee.advance_salaries.filter(status='Approved').order_by('created_at'):
        remaining = adv.remaining_amount
        monthly   = adv.effective_monthly_deduction
        if remaining > 0 and monthly and monthly > 0:
            return round(min(monthly, remaining), 2), adv
    return 0.0, None


def _sync_advance_deductions(run):
    """Refresh advance deductions on a DRAFT run from current approved advances.

    Confirmed runs are locked snapshots and are never modified. Because
    remaining_amount only counts *confirmed* deductions, re-syncing a draft is
    idempotent and never double-counts.
    """
    if run.status != 'Draft':
        return
    for entry in run.entries.select_related('employee'):
        advance_ded, advance_obj = _pick_active_advance(entry.employee)
        advance_obj_pk = advance_obj.pk if advance_obj else None
        if round(entry.advance_deduction, 2) != advance_ded or entry.advance_salary_id != advance_obj_pk:
            entry.advance_deduction = advance_ded
            entry.advance_salary    = advance_obj
            entry.compute_and_save()


@login_required
def payroll_detail(request, pk):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    run = get_object_or_404(PayrollRun, pk=pk)

    # Draft runs auto-refresh advance + attendance deductions so later edits appear
    _sync_advance_deductions(run)
    _sync_attendance_deductions(run)

    entries = run.entries.select_related(
        'employee', 'employee__department', 'employee__mol', 'advance_salary'
    ).order_by('employee__mol__mol', 'employee__emp_name')

    # Pre-group by MOL with subtotals so the template can render them
    mol_groups = []
    for entry in entries:
        mol = entry.employee.mol
        mol_key = mol.pk if mol else None
        mol_label = mol.mol if mol else 'No MOL Assigned'
        if mol_groups and mol_groups[-1]['mol_key'] == mol_key:
            mol_groups[-1]['entries'].append(entry)
            mol_groups[-1]['total_gross'] = round(mol_groups[-1]['total_gross'] + entry.gross_salary, 2)
            mol_groups[-1]['total_net']   = round(mol_groups[-1]['total_net']   + entry.net_salary, 2)
        else:
            mol_groups.append({
                'mol_key':    mol_key,
                'mol_label':  mol_label,
                'entries':    [entry],
                'total_gross': round(entry.gross_salary, 2),
                'total_net':   round(entry.net_salary, 2),
            })

    return render(request, 'hr_de/payroll/payroll_detail.html', {
        'run':        run,
        'entries':    entries,
        'mol_groups': mol_groups,
    })


@login_required
def payroll_entry_update(request, entry_pk):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    entry = get_object_or_404(PayrollEntry, pk=entry_pk)

    if entry.payroll_run.status == 'Confirmed':
        messages.error(request, "Cannot edit a confirmed payroll run.")
        return redirect('payroll_detail', pk=entry.payroll_run.pk)

    if request.method == 'POST':
        def _f(k):
            try: return float(request.POST.get(k, 0) or 0)
            except ValueError: return 0.0

        entry.bonus           = _f('bonus')
        entry.overtime_pay    = _f('overtime_pay')
        entry.other_additions = _f('other_additions')
        entry.loan_deduction  = _f('loan_deduction')
        entry.other_deductions= _f('other_deductions')
        entry.notes           = request.POST.get('notes', '')
        entry.compute_and_save()
        messages.success(request, f"Updated payroll entry for {entry.employee.emp_name}.")
        return redirect('payroll_detail', pk=entry.payroll_run.pk)

    # GET: refresh the attendance deduction from the current sheet so it displays live
    if entry.payroll_run.status == 'Draft':
        absent, half, ded = _attendance_deduction_for(
            entry.employee, entry.payroll_run.year, entry.payroll_run.month, entry.gross_salary or 0
        )
        if (entry.absent_days != absent or entry.half_days != half
                or round(entry.attendance_deduction, 2) != round(ded, 2)):
            entry.absent_days          = absent
            entry.half_days            = half
            entry.attendance_deduction = ded
            entry.compute_and_save()

    return render(request, 'hr_de/payroll/payroll_entry_edit.html', {'entry': entry})


@login_required
def payroll_delete(request, pk):
    """Delete an entire Draft payroll run."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    run = get_object_or_404(PayrollRun, pk=pk)
    if run.status == 'Confirmed':
        messages.error(request, 'Cannot delete a confirmed payroll run.')
        return redirect('payroll_detail', pk=pk)
    if request.method == 'POST':
        label = str(run)
        run.delete()
        messages.success(request, f'{label} has been deleted.')
        return redirect('payroll_list')
    return render(request, 'hr_de/payroll/payroll_delete_confirm.html', {'run': run})


@login_required
def payroll_entry_remove(request, entry_pk):
    """Remove a single employee entry from a Draft payroll run."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    entry = get_object_or_404(PayrollEntry, pk=entry_pk)
    if entry.payroll_run.status == 'Confirmed':
        messages.error(request, 'Cannot remove entries from a confirmed payroll run.')
        return redirect('payroll_detail', pk=entry.payroll_run.pk)
    if request.method == 'POST':
        run_pk = entry.payroll_run.pk
        emp_name = entry.employee.emp_name
        entry.delete()
        messages.success(request, f'Removed {emp_name} from the payroll run.')
        return redirect('payroll_detail', pk=run_pk)
    return redirect('payroll_detail', pk=entry.payroll_run.pk)


@login_required
def payroll_confirm(request, pk):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    run = get_object_or_404(PayrollRun, pk=pk)
    if request.method == 'POST':
        if run.status == 'Confirmed':
            messages.info(request, "Already confirmed.")
        else:
            run.status = 'Confirmed'
            run.confirmed_at = timezone.now()
            run.save()
            messages.success(request, f"{run} has been confirmed and locked.")
    return redirect('payroll_detail', pk=pk)


@login_required
def payslip(request, entry_pk):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    entry = get_object_or_404(
        PayrollEntry.objects.select_related('employee', 'employee__department', 'payroll_run'),
        pk=entry_pk
    )
    return render(request, 'hr_de/payroll/payslip.html', {'entry': entry})


############ ADVANCE SALARY ############

@login_required
def advance_apply(request):
    """Submit a new advance salary application."""
    try:
        user_role = request.user.role.role
    except Exception:
        user_role = None

    # Determine which employees are selectable
    if user_role == 'HR':
        employees = Employee.objects.filter(is_active=True).order_by('emp_name')
    elif user_role == 'Head':
        dept = request.user.role.department
        employees = Employee.objects.filter(is_active=True, department=dept).order_by('emp_name') if dept else Employee.objects.none()
    else:
        # Regular employee — can only apply for themselves
        try:
            employees = [request.user.employee]
        except Exception:
            return render(request, 'hr_de/unauthorized.html', status=403)

    if request.method == 'POST':
        emp_pk      = request.POST.get('employee')
        amount_raw  = request.POST.get('amount', '').strip()
        reason      = request.POST.get('reason', '').strip()
        monthly_raw = request.POST.get('requested_monthly_deduction', '').strip()

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Please enter a valid positive amount.')
            return redirect('advance_apply')

        try:
            req_monthly = float(monthly_raw)
            if req_monthly <= 0 or req_monthly > amount:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Monthly deduction must be a positive value and not exceed the advance amount.')
            return redirect('advance_apply')

        if not reason:
            messages.error(request, 'Reason is required.')
            return redirect('advance_apply')

        if user_role in ('HR', 'Head'):
            employee = get_object_or_404(Employee, pk=emp_pk)
        else:
            employee = request.user.employee

        # Head applying on behalf → auto-approve Head stage (keeps requested amount)
        if user_role == 'Head':
            initial_status  = 'Head_Approved'
            head_approved_by = request.user
            head_approved_at = timezone.now()
            approved_monthly = req_monthly
        else:
            initial_status   = 'Pending'
            head_approved_by = None
            head_approved_at = None
            approved_monthly = None

        AdvanceSalary.objects.create(
            employee                    = employee,
            amount                      = amount,
            reason                      = reason,
            requested_monthly_deduction = req_monthly,
            approved_monthly_deduction  = approved_monthly,
            status                      = initial_status,
            head_approved_by            = head_approved_by,
            head_approved_at            = head_approved_at,
            applied_by                  = request.user,
        )
        messages.success(request, f'Advance salary application submitted for {employee.emp_name}.')
        if user_role == 'HR':
            return redirect('advance_list')
        elif user_role == 'Head':
            return redirect('advance_pending')
        else:
            return redirect('my_advances')

    return render(request, 'hr_de/advance_salary/apply.html', {'employees': employees, 'user_role': user_role})


@login_required
def advance_pending(request):
    """Pending queue — Head sees Pending for their dept; HR sees Head_Approved."""
    try:
        user_role = request.user.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    if user_role.role == 'Head':
        dept    = user_role.department
        advances = AdvanceSalary.objects.filter(
            status='Pending', employee__department=dept
        ).select_related('employee', 'employee__department') if dept else AdvanceSalary.objects.none()
    elif user_role.role == 'HR':
        advances = AdvanceSalary.objects.filter(
            status='Head_Approved'
        ).select_related('employee', 'employee__department', 'head_approved_by')
    else:
        return render(request, 'hr_de/unauthorized.html', status=403)

    return render(request, 'hr_de/advance_salary/pending.html', {
        'advances':  advances,
        'user_role': user_role,
    })


@login_required
def advance_approve(request, pk):
    """Approve or reject a single advance salary application."""
    try:
        user_role = request.user.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    advance = get_object_or_404(AdvanceSalary, pk=pk)

    if request.method == 'POST':
        action           = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason', '').strip()

        def _approved_amount(default):
            try:
                val = float(request.POST.get('approved_monthly_deduction', '') or default)
                return round(val, 2) if val > 0 else round(float(default), 2)
            except (ValueError, TypeError):
                return round(float(default), 2)

        if user_role.role == 'Head':
            if advance.status != 'Pending':
                messages.error(request, 'This application is no longer pending for Head approval.')
                return redirect('advance_pending')
            if advance.employee.department != user_role.department:
                return render(request, 'hr_de/unauthorized.html', status=403)
            if action == 'approve':
                approved_amt = _approved_amount(advance.requested_monthly_deduction)
                advance.status           = 'Head_Approved'
                advance.head_approved_by = request.user
                advance.head_approved_at = timezone.now()
                advance.save()
                # Set + log the monthly deduction (logs only if it differs)
                advance.set_monthly_deduction(approved_amt, request.user, 'Head', note='Set at Head approval')
            elif action == 'reject':
                advance.status           = 'Rejected'
                advance.head_approved_by = request.user
                advance.rejection_reason = rejection_reason
                advance.save()

        elif user_role.role == 'HR':
            if advance.status != 'Head_Approved':
                messages.error(request, 'This application must be approved by the Head first.')
                return redirect('advance_pending')
            if action == 'approve':
                approved_amt = _approved_amount(advance.effective_monthly_deduction)
                advance.status        = 'Approved'
                advance.hr_approved_by = request.user
                advance.hr_approved_at = timezone.now()
                advance.save()
                advance.set_monthly_deduction(approved_amt, request.user, 'HR', note='Set at HR final approval')
            elif action == 'reject':
                advance.status        = 'Rejected'
                advance.hr_approved_by = request.user
                advance.rejection_reason = rejection_reason
                advance.save()
        else:
            return render(request, 'hr_de/unauthorized.html', status=403)

        messages.success(request, f'Application for {advance.employee.emp_name} has been {advance.status.lower().replace("_", " ")}.')
        return redirect('advance_pending')

    return render(request, 'hr_de/advance_salary/approve.html', {
        'advance':   advance,
        'user_role': user_role,
    })


@login_required
def advance_edit_deduction(request, pk):
    """Ongoing edit of the monthly deduction — HR (any) or Head (their dept)."""
    try:
        user_role = request.user.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    advance = get_object_or_404(
        AdvanceSalary.objects.select_related('employee', 'employee__department'), pk=pk
    )

    # Permission: HR any; Head only their own department
    if user_role.role == 'HR':
        pass
    elif user_role.role == 'Head':
        if advance.employee.department != user_role.department:
            return render(request, 'hr_de/unauthorized.html', status=403)
    else:
        return render(request, 'hr_de/unauthorized.html', status=403)

    # Cannot edit a rejected application
    if advance.status == 'Rejected':
        messages.error(request, 'Cannot edit the deduction of a rejected application.')
        return redirect('advance_list')

    if request.method == 'POST':
        note = request.POST.get('note', '').strip()
        try:
            new_amt = float(request.POST.get('approved_monthly_deduction', ''))
            if new_amt <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Enter a valid positive monthly deduction amount.')
            return redirect('advance_edit_deduction', pk=pk)

        if new_amt > advance.remaining_amount and advance.status == 'Approved':
            messages.error(request, f'Monthly deduction cannot exceed the remaining balance (AED {advance.remaining_amount:.2f}).')
            return redirect('advance_edit_deduction', pk=pk)

        advance.set_monthly_deduction(new_amt, request.user, user_role.role, note=note)
        messages.success(request, f'Monthly deduction for {advance.employee.emp_name} updated to AED {new_amt:.2f}.')
        return redirect('advance_edit_deduction', pk=pk)

    changes = advance.deduction_changes.select_related('changed_by').all()
    return render(request, 'hr_de/advance_salary/edit_deduction.html', {
        'advance':   advance,
        'user_role': user_role,
        'changes':   changes,
    })


@login_required
def advance_list(request):
    """Full history — HR sees all; Head sees their own department."""
    try:
        role_obj  = request.user.role
        user_role = role_obj.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    if user_role not in ('HR', 'Head'):
        return render(request, 'hr_de/unauthorized.html', status=403)

    status_filter = request.GET.get('status', '')
    query         = request.GET.get('q', '')

    advances = AdvanceSalary.objects.select_related(
        'employee', 'employee__department', 'head_approved_by', 'hr_approved_by'
    )

    # Head is scoped to their own department
    if user_role == 'Head':
        dept = role_obj.department
        advances = advances.filter(employee__department=dept) if dept else advances.none()

    if status_filter:
        advances = advances.filter(status=status_filter)
    if query:
        advances = advances.filter(
            Q(employee__emp_name__icontains=query) |
            Q(employee__emp_id__icontains=query)
        )

    return render(request, 'hr_de/advance_salary/list.html', {
        'advances':        advances,
        'status_choices':  AdvanceSalary.STATUS_CHOICES,
        'selected_status': status_filter,
        'query':           query,
        'user_role':       user_role,
    })


@login_required
def my_advances(request):
    """Employee's own advance history."""
    try:
        employee = request.user.employee
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    advances = AdvanceSalary.objects.filter(employee=employee)
    return render(request, 'hr_de/advance_salary/my_advances.html', {
        'employee': employee,
        'advances': advances,
    })


############ PASSPORT REQUESTS ############

@login_required
def passport_apply(request):
    """Submit a passport request. HR can pick any employee; others apply for self."""
    try:
        user_role = request.user.role.role
    except Exception:
        user_role = None

    if user_role == 'HR':
        employees = Employee.objects.filter(is_active=True).order_by('emp_name')
    elif user_role == 'Head':
        dept = request.user.role.department
        employees = Employee.objects.filter(is_active=True, department=dept).order_by('emp_name') if dept else Employee.objects.none()
    else:
        try:
            employees = [request.user.employee]
        except Exception:
            return render(request, 'hr_de/unauthorized.html', status=403)

    if request.method == 'POST':
        emp_pk          = request.POST.get('employee')
        reason          = request.POST.get('reason', '').strip()
        needed_from     = _parse_date(request.POST.get('needed_from') or None)
        expected_return = _parse_date(request.POST.get('expected_return') or None)

        if not reason:
            messages.error(request, 'Reason is required.')
            return redirect('passport_apply')

        if user_role == 'HR':
            employee = get_object_or_404(Employee, pk=emp_pk)
        elif user_role == 'Head':
            # Head can only request on behalf of employees in their own department
            dept = request.user.role.department
            employee = get_object_or_404(Employee, pk=emp_pk, department=dept)
        else:
            employee = request.user.employee

        PassportRequest.objects.create(
            employee        = employee,
            reason          = reason,
            needed_from     = needed_from,
            expected_return = expected_return,
            applied_by      = request.user,
        )
        messages.success(request, f'Passport request submitted for {employee.emp_name}.')
        return redirect('passport_list' if user_role in ('HR', 'Head') else 'my_passport_requests')

    return render(request, 'hr_de/passport/apply.html', {
        'employees': employees,
        'user_role': user_role,
    })


@login_required
def passport_pending(request):
    """HR queue of pending passport requests."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    requests_qs = PassportRequest.objects.filter(status='Pending').select_related(
        'employee', 'employee__department'
    )
    return render(request, 'hr_de/passport/pending.html', {'requests': requests_qs})


@login_required
def passport_approve(request, pk):
    """HR approves or rejects a passport request."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    req = get_object_or_404(PassportRequest.objects.select_related('employee'), pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if req.status != 'Pending':
            messages.error(request, 'This request has already been processed.')
            return redirect('passport_pending')

        if action == 'approve':
            req.status      = 'Approved'
            req.approved_by = request.user
            req.approved_at = timezone.now()
            req.save()
            # Passport is now physically with the employee
            req.employee.passport_status = 'With employee'
            req.employee.save(update_fields=['passport_status'])
            messages.success(request, f'Passport request for {req.employee.emp_name} approved.')
        elif action == 'reject':
            req.status           = 'Rejected'
            req.approved_by      = request.user
            req.approved_at      = timezone.now()
            req.rejection_reason = request.POST.get('rejection_reason', '').strip()
            req.save()
            messages.success(request, f'Passport request for {req.employee.emp_name} rejected.')
        return redirect('passport_pending')

    return render(request, 'hr_de/passport/approve.html', {'req': req})


@login_required
def passport_mark_returned(request, pk):
    """HR marks an approved passport as returned to the company."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    req = get_object_or_404(PassportRequest.objects.select_related('employee'), pk=pk)
    if request.method == 'POST':
        if req.status != 'Approved':
            messages.error(request, 'Only an approved (outstanding) request can be marked returned.')
            return redirect('passport_list')
        req.status             = 'Returned'
        req.returned_at        = timezone.now()
        req.returned_marked_by = request.user
        req.save()
        req.employee.passport_status = 'With company'
        req.employee.save(update_fields=['passport_status'])
        messages.success(request, f"{req.employee.emp_name}'s passport has been returned and is back with the company.")
    # Return to wherever the action was triggered (outstanding page or full list)
    next_url = request.POST.get('next')
    if next_url == 'outstanding':
        return redirect('passport_outstanding')
    return redirect('passport_list')


@login_required
def passport_outstanding(request):
    """Passports currently OUT — any employee whose custody is 'With employee'.

    Includes employees set manually via the employee edit form (no request)
    as well as those approved through a passport request.
    """
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    from datetime import date

    employees_out = Employee.objects.filter(
        passport_status='With employee'
    ).select_related('department').order_by('emp_name')

    items = []
    for emp in employees_out:
        req = emp.passport_requests.filter(status='Approved').order_by('-approved_at').first()
        items.append({'employee': emp, 'request': req})

    return render(request, 'hr_de/passport/outstanding.html', {
        'items': items,
        'today': date.today(),
    })


@login_required
def passport_employee_return(request, emp_pk):
    """Mark an employee's passport as returned to the company.

    Flips custody back to 'With company' and closes any open approved request.
    Works whether or not a passport request exists.
    """
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)
    emp = get_object_or_404(Employee, pk=emp_pk)
    if request.method == 'POST':
        for req in emp.passport_requests.filter(status='Approved'):
            req.status             = 'Returned'
            req.returned_at        = timezone.now()
            req.returned_marked_by = request.user
            req.save()
        emp.passport_status = 'With company'
        emp.save(update_fields=['passport_status'])
        messages.success(request, f"{emp.emp_name}'s passport has been returned and is back with the company.")
    return redirect('passport_outstanding')


@login_required
def passport_list(request):
    """Passport request history. HR sees all; Head sees their own department."""
    try:
        role_obj  = request.user.role
        user_role = role_obj.role
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)

    if user_role not in ('HR', 'Head'):
        return render(request, 'hr_de/unauthorized.html', status=403)

    status_filter = request.GET.get('status', '')
    query         = request.GET.get('q', '')

    requests_qs = PassportRequest.objects.select_related(
        'employee', 'employee__department', 'approved_by'
    )

    # Head is scoped to their own department
    if user_role == 'Head':
        dept = role_obj.department
        requests_qs = requests_qs.filter(employee__department=dept) if dept else requests_qs.none()

    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)
    if query:
        requests_qs = requests_qs.filter(
            Q(employee__emp_name__icontains=query) |
            Q(employee__emp_id__icontains=query)
        )

    return render(request, 'hr_de/passport/list.html', {
        'requests':        requests_qs,
        'status_choices':  PassportRequest.STATUS_CHOICES,
        'selected_status': status_filter,
        'query':           query,
        'user_role':       user_role,
    })


@login_required
def my_passport_requests(request):
    """Employee's own passport requests."""
    try:
        employee = request.user.employee
    except Exception:
        return render(request, 'hr_de/unauthorized.html', status=403)
    requests_qs = PassportRequest.objects.filter(employee=employee)
    return render(request, 'hr_de/passport/my_requests.html', {
        'employee': employee,
        'requests': requests_qs,
    })


#######################  AUTHENTICATION VIEWS #######################
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        email = request.POST.get('email')
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('signup')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')
        user = User.objects.create_user(username=username, password=password, first_name=first_name)
        login(request, user)
        return redirect('home')  # Change to your homepage view name
    return render(request, 'hr_de/auth/signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            user_role = getattr(user, 'role', None)
            user_employee = getattr(user, 'employee', None)

            if not user_role and not user_employee:
                messages.error(request, "You do not have permission to access the HR module.")
                return redirect('login')

            login(request, user)

            if user_role:
                if user_role.role == 'Head':
                    return redirect('employee_home')
                return redirect('home')
            # Regular employee (no Role) → self-service dashboard
            return redirect('employee_dashboard')
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'hr_de/auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
import random
import string

def generate_random_password():
    # Generate 4 random digits
    digits = ''.join(random.choices(string.digits, k=4))
    # Combine with 'junaid'
    return f'junaid{digits}'

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            new_password = generate_random_password()
            user.set_password(new_password)
            user.save()

            send_mail(
                subject='Your New Password',
                message=f'Username: {user.username} Your new login password is: {new_password}',
                from_email='noreply@example.com',
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, 'New password sent to your email.')
            return redirect('forgot_password')
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist.')
    return render(request, 'hr_de/auth/forgot_password.html')

# ── DOCUMENT EXPIRY NOTIFICATION HELPERS ────────────────────────────────────

_DOC_FIELDS = [
    ('PASSPORT',        'passport_expiry',        'Passport',        'fas fa-passport'),
    ('VISA',            'visa_expiry',             'Visa',            'fas fa-stamp'),
    ('EID',             'eid_expiry',              'Emirates ID',     'fas fa-id-card'),
    ('LABOUR_CARD',     'labour_card_expiry',      'Labour Card',     'fas fa-briefcase'),
    ('INSURANCE',       'insurance_expiry',        'Insurance',       'fas fa-shield-halved'),
    ('DRIVING_LICENSE', 'driving_license_expiry',  'Driving License', 'fas fa-car'),
]


_MOL_DOC_FIELDS = [
    ('MOL_TRADE_LICENSE', 'trade_license_expiry',      'Trade License'),
    ('MOL_TENANCY',       'tenancy_contract_expiry',   'Tenancy Contract'),
    ('MOL_ESTABLISHMENT', 'establishment_card_expiry', 'Establishment Card'),
]


def _expiry_urgency_and_text(expiry, today, label, subject):
    days_left = (expiry - today).days
    if days_left < 0:
        urgency = 'critical'
        title   = f"{label} EXPIRED — {subject}"
        message = (
            f"{subject}'s {label} expired on {expiry.strftime('%d %b %Y')} "
            f"({abs(days_left)} day{'s' if abs(days_left) != 1 else ''} ago)."
        )
    elif days_left <= 7:
        urgency = 'critical'
        title   = f"{label} expiring in {days_left} day{'s' if days_left != 1 else ''} — {subject}"
        message = (
            f"{subject}'s {label} expires on {expiry.strftime('%d %b %Y')} "
            f"— only {days_left} day{'s' if days_left != 1 else ''} remaining."
        )
    elif days_left <= 30:
        urgency = 'warning'
        title   = f"{label} expiring soon — {subject}"
        message = (
            f"{subject}'s {label} expires on {expiry.strftime('%d %b %Y')} "
            f"({days_left} days left)."
        )
    else:
        urgency = 'info'
        title   = f"{label} expiry notice — {subject}"
        message = (
            f"{subject}'s {label} expires on {expiry.strftime('%d %b %Y')} "
            f"({days_left} days left)."
        )
    return days_left, urgency, title, message


def _generate_expiry_notifications():
    today = timezone.now().date()

    # ── Employee document expiries ───────────────────────────────────────────
    for emp in Employee.objects.filter(is_active=True).select_related('department'):
        for doc_key, expiry_field, doc_label, _ in _DOC_FIELDS:
            expiry = getattr(emp, expiry_field, None)
            if not expiry:
                continue
            days_left = (expiry - today).days
            if days_left > 60:
                continue

            _, urgency, title, message = _expiry_urgency_and_text(expiry, today, doc_label, emp.emp_name)

            existing = Notification.objects.filter(
                employee=emp, doc_type=doc_key,
                category='document_expiry', is_read=False,
            ).first()

            if existing:
                if existing.urgency != urgency or existing.title != title:
                    existing.urgency = urgency
                    existing.title   = title
                    existing.message = message
                    existing.save()
            else:
                Notification.objects.create(
                    employee=emp, title=title, message=message,
                    category='document_expiry', urgency=urgency, doc_type=doc_key,
                )

    # ── MOL document expiries ────────────────────────────────────────────────
    for mol in Mol.objects.all():
        for doc_key, expiry_field, doc_label in _MOL_DOC_FIELDS:
            expiry = getattr(mol, expiry_field, None)
            if not expiry:
                continue
            days_left = (expiry - today).days
            if days_left > 60:
                continue

            _, urgency, title, message = _expiry_urgency_and_text(expiry, today, doc_label, mol.mol)

            existing = Notification.objects.filter(
                mol=mol, doc_type=doc_key,
                category='mol_document_expiry', is_read=False,
            ).first()

            if existing:
                if existing.urgency != urgency or existing.title != title:
                    existing.urgency = urgency
                    existing.title   = title
                    existing.message = message
                    existing.save()
            else:
                Notification.objects.create(
                    mol=mol, title=title, message=message,
                    category='mol_document_expiry', urgency=urgency, doc_type=doc_key,
                )


def _cleanup_old_read_notifications():
    """Delete read notifications older than 30 days."""
    cutoff = timezone.now() - timezone.timedelta(days=30)
    Notification.objects.filter(is_read=True, created_at__lt=cutoff).delete()


@login_required
def notification_list(request):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    _generate_expiry_notifications()

    _urgency_rank = {'critical': 0, 'warning': 1, 'info': 2}
    unread = sorted(
        Notification.objects.filter(is_read=False)
            .select_related('employee', 'employee__department'),
        key=lambda n: _urgency_rank.get(n.urgency, 3),
    )
    read = list(
        Notification.objects.filter(is_read=True)
            .select_related('employee', 'employee__department')
            .order_by('-created_at')[:50]
    )

    critical_count = sum(1 for n in unread if n.urgency == 'critical')
    warning_count  = sum(1 for n in unread if n.urgency == 'warning')

    return render(request, 'hr_de/notifications.html', {
        'unread':         unread,
        'read':           read,
        'unread_count':   len(unread),
        'critical_count': critical_count,
        'warning_count':  warning_count,
    })


@require_POST
def mark_notification_read(request, pk):
    try:
        n = Notification.objects.get(pk=pk)
        n.is_read = True
        n.save()
        _cleanup_old_read_notifications()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)


@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)
    _cleanup_old_read_notifications()
    return JsonResponse({'status': 'success'})


############ BULK UPLOAD EMPLOYEE DATA ############

import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from .models import Employee, Mol
from django.contrib import messages

_BULK_COLUMNS = [
    ("EMP ID",                  "Required – unique employee code (e.g. EMP001)"),
    ("EMP NAME",                "Required – full name"),
    ("DOB",                     "Required – date of birth (YYYY-MM-DD)"),
    ("GENDER",                  "M or F"),
    ("NATIONALITY",             "Country code e.g. IN, AE, PH"),
    ("CONTACT NUMBER",          "Mobile / phone number"),
    ("DEPT",                    "Must match an existing Department name"),
    ("DESIGNATION",             "Job title"),
    ("MOL",                     "Ministry of Labour / sub-company name"),
    ("DATE OF JOIN",            "Joining date (YYYY-MM-DD)"),
    ("SALARY",                  "Monthly gross salary (number)"),
    ("LOCATION",                "Work location / site"),
    ("EMPLOYEE STATUS",         "Active | Inactive | On Leave | Resigned | Terminated"),
    ("IS ACTIVE",               "YES or NO"),
    ("PASSPORT STATUS",         "With company | With employee"),
    ("PASSPORT NO.",            "Passport number"),
    ("PASSPORT EXPIRY",         "YYYY-MM-DD"),
    ("LABOUR NO",               "Labour / work permit number"),
    ("LABOUR EXPIRY",           "YYYY-MM-DD"),
    ("EID NO",                  "Emirates ID number"),
    ("EID EXPIRY",              "YYYY-MM-DD"),
    ("VISA EXPIRY",             "YYYY-MM-DD"),
    ("INSURANCE NO",            "Insurance policy number"),
    ("INSURANCE EXPIRY",        "YYYY-MM-DD"),
    ("DRIVING LICENSE NO",      "Driving licence number"),
    ("DRIVING LICENSE EXPIRY",  "YYYY-MM-DD"),
    # Login account — leave blank to skip account creation
    ("USERNAME",                "Optional – login username. Leave blank to skip account creation."),
    ("PASSWORD",                "Optional – initial password. Required if USERNAME is filled."),
]

# Column indices (0-based) that hold login credentials — styled differently in the template
_ACCOUNT_COL_NAMES = {"USERNAME", "PASSWORD"}

def _parse_date(val):
    if pd.isnull(val):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None

def download_employee_template(request):
    """Return a pre-formatted .xlsx template the user fills in and uploads."""
    from openpyxl import Workbook
    from openpyxl.styles import (
        PatternFill, Font, Alignment, Border, Side
    )
    from django.http import HttpResponse

    wb = Workbook()
    ws = wb.active
    ws.title = "Employees"

    header_fill   = PatternFill("solid", fgColor="1E3A5F")
    acct_fill     = PatternFill("solid", fgColor="7C3AED")   # purple for account cols
    note_fill     = PatternFill("solid", fgColor="EBF3FF")
    acct_note_fill= PatternFill("solid", fgColor="F3E8FF")   # light purple note
    sample_fill   = PatternFill("solid", fgColor="F0FFF4")
    header_font   = Font(bold=True, color="FFFFFF", size=11)
    note_font     = Font(italic=True, color="1E3A5F", size=9)
    acct_note_font= Font(italic=True, color="6D28D9", size=9)
    sample_font   = Font(color="1E3A5F", size=10)
    thin_border   = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    headers = [col for col, _ in _BULK_COLUMNS]
    notes   = [note for _, note in _BULK_COLUMNS]

    # Row 1 – column headers
    for col_idx, header in enumerate(headers, start=1):
        is_acct = header in _ACCOUNT_COL_NAMES
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill      = acct_fill if is_acct else header_fill
        cell.font      = header_font
        cell.alignment = center
        cell.border    = thin_border

    # Row 2 – notes / instructions
    for col_idx, (header, note) in enumerate(_BULK_COLUMNS, start=1):
        is_acct = header in _ACCOUNT_COL_NAMES
        cell = ws.cell(row=2, column=col_idx, value=note)
        cell.fill      = acct_note_fill if is_acct else note_fill
        cell.font      = acct_note_font if is_acct else note_font
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border    = thin_border

    # Row 3 – sample data
    sample = [
        "EMP001", "Ali Hassan", "1990-06-15", "M", "AE", "0501234567",
        "Sales", "Sales Manager", "ABC Trading LLC", "2023-01-01",
        "8000", "Dubai", "Active", "YES", "With company",
        "P12345678", "2028-06-15", "LC123456", "2025-06-30",
        "784-1990-1234567-1", "2027-03-15", "2025-12-31",
        "INS001", "2026-06-01", "DL123456", "2027-01-01",
        "ali.hassan", "Pass@1234",
    ]
    for col_idx, (val, (header, _)) in enumerate(zip(sample, _BULK_COLUMNS), start=1):
        is_acct = header in _ACCOUNT_COL_NAMES
        cell = ws.cell(row=3, column=col_idx, value=val)
        cell.fill      = PatternFill("solid", fgColor="EDE9FE") if is_acct else sample_fill
        cell.font      = Font(color="6D28D9", size=10) if is_acct else sample_font
        cell.border    = thin_border

    # Row heights & column widths
    ws.row_dimensions[1].height = 28
    ws.row_dimensions[2].height = 40
    ws.row_dimensions[3].height = 22
    ws.freeze_panes = "A4"

    col_widths = [12, 22, 14, 8, 14, 16, 18, 18, 22, 14,
                  10, 14, 16, 10, 18, 16, 16, 14, 14, 22, 14, 14, 14, 16, 18, 20,
                  18, 16]
    for i, width in enumerate(col_widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="employee_upload_template.xlsx"'
    wb.save(response)
    return response


def bulk_upload_employees(request):
    if request.method == "POST" and request.FILES.get("excel_file"):
        excel_file = request.FILES["excel_file"]
        try:
            df = pd.read_excel(excel_file, header=0, skiprows=[1])  # skip the notes row

            created_count    = 0
            updated_count    = 0
            accounts_created = 0
            error_rows       = []

            for index, row in df.iterrows():
                try:
                    emp_id = str(row.get("EMP ID") or '').strip()
                    if not emp_id or emp_id.lower() == 'nan':
                        continue

                    mol_name = str(row.get("MOL") or '').strip()
                    mol_obj = None
                    if mol_name and mol_name.lower() != 'nan':
                        mol_obj, _ = Mol.objects.get_or_create(mol=mol_name)

                    dept_name = str(row.get("DEPT") or '').strip()
                    dept_obj = None
                    if dept_name and dept_name.lower() != 'nan':
                        dept_obj = Department.objects.filter(name__iexact=dept_name).first()

                    is_active_raw = str(row.get("IS ACTIVE") or 'YES').strip().upper()
                    is_active = is_active_raw not in ('NO', 'FALSE', '0', 'N')

                    gender_raw = str(row.get("GENDER") or 'M').strip().upper()
                    gender = gender_raw if gender_raw in ('M', 'F') else 'M'

                    status_raw = str(row.get("EMPLOYEE STATUS") or 'Active').strip()
                    valid_statuses = [c[0] for c in Employee.EMPLOYEE_STATUS_CHOICES]
                    employee_status = status_raw if status_raw in valid_statuses else 'Active'

                    def _str(key):
                        val = row.get(key)
                        if val is None or (isinstance(val, float) and pd.isnull(val)):
                            return None
                        return str(val).strip() or None

                    emp_obj, created = Employee.objects.update_or_create(
                        emp_id=emp_id,
                        defaults={
                            "emp_name":               str(row.get("EMP NAME") or '').strip(),
                            "dob":                    _parse_date(row.get("DOB")),
                            "gender":                 gender,
                            "nationality":            _str("NATIONALITY") or "IN",
                            "contact_number":         _str("CONTACT NUMBER"),
                            "department":             dept_obj,
                            "designation":            _str("DESIGNATION"),
                            "mol":                    mol_obj,
                            "joining_date":           _parse_date(row.get("DATE OF JOIN")),
                            "emp_salary":             row.get("SALARY") or None,
                            "job_location":           _str("LOCATION"),
                            "employee_status":        employee_status,
                            "is_active":              is_active,
                            "passport_status":        _str("PASSPORT STATUS") or "With company",
                            "passport_number":        _str("PASSPORT NO."),
                            "passport_expiry":        _parse_date(row.get("PASSPORT EXPIRY")),
                            "labour_card_number":     _str("LABOUR NO"),
                            "labour_card_expiry":     _parse_date(row.get("LABOUR EXPIRY")),
                            "eid_number":             _str("EID NO"),
                            "eid_expiry":             _parse_date(row.get("EID EXPIRY")),
                            "visa_expiry":            _parse_date(row.get("VISA EXPIRY")),
                            "insurance_number":       _str("INSURANCE NO"),
                            "insurance_expiry":       _parse_date(row.get("INSURANCE EXPIRY")),
                            "driving_license_number": _str("DRIVING LICENSE NO"),
                            "driving_license_expiry": _parse_date(row.get("DRIVING LICENSE EXPIRY")),
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    # ── Login account creation ───────────────────────────────
                    username = _str("USERNAME")
                    password = _str("PASSWORD")
                    if username and password:
                        if emp_obj.user_id:
                            # Employee already has an account — leave it alone
                            pass
                        elif User.objects.filter(username=username).exists():
                            error_rows.append(
                                f"Row {index + 3} ({emp_id}): username '{username}' is already taken — account not created."
                            )
                        else:
                            new_user = User.objects.create_user(
                                username=username,
                                password=password,
                                first_name=emp_obj.emp_name,
                            )
                            emp_obj.user = new_user
                            emp_obj.save(update_fields=["user"])
                            accounts_created += 1

                except Exception as e:
                    error_rows.append(f"Row {index + 3}: {e}")

            if error_rows:
                for err in error_rows:
                    messages.error(request, err)

            if created_count or updated_count:
                acct_note = f", {accounts_created} account{'s' if accounts_created != 1 else ''} created" if accounts_created else ""
                messages.success(
                    request,
                    f"Upload complete — {created_count} created, {updated_count} updated{acct_note}."
                )
            return redirect("employee_upload")

        except Exception as e:
            messages.error(request, f"Upload failed: {e}")

    columns = [col for col, _ in _BULK_COLUMNS]
    return render(request, "hr_de/employee_bulk_upload.html", {"columns": columns})


# ── MD System Account Management (HR only) ──────────────────────────────────

@login_required
def md_account_list(request):
    try:
        caller_role = request.user.role.role
    except Exception:
        caller_role = None
    if caller_role != 'HR':
        return render(request, 'hr_de/unauthorized.html', status=403)

    md_roles = Role.objects.filter(role='MD').select_related('user')
    return render(request, 'hr_de/md_accounts.html', {'md_roles': md_roles})


@login_required
def md_account_create(request):
    try:
        caller_role = request.user.role.role
    except Exception:
        caller_role = None
    if caller_role != 'HR':
        return render(request, 'hr_de/unauthorized.html', status=403)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        full_name = request.POST.get('full_name', '').strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return redirect('md_account_list')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return redirect('md_account_list')

        new_user = User.objects.create_user(
            username=username,
            password=password,
            first_name=full_name,
        )
        Role.objects.create(user=new_user, role='MD')
        messages.success(request, f"MD account '{username}' created successfully.")
        return redirect('md_account_list')

    return redirect('md_account_list')


@login_required
def md_account_delete(request, pk):
    try:
        caller_role = request.user.role.role
    except Exception:
        caller_role = None
    if caller_role != 'HR':
        return render(request, 'hr_de/unauthorized.html', status=403)

    role_obj = get_object_or_404(Role, pk=pk, role='MD')
    user_obj = role_obj.user
    username = user_obj.username if user_obj else '—'
    user_obj.delete()
    messages.success(request, f"MD account '{username}' deleted.")
    return redirect('md_account_list')


# ── SALARY REVISION (AUDIT TRAIL) ────────────────────────────────────────────

@login_required
def salary_revision_create(request, emp_id):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    employee  = get_object_or_404(Employee, pk=emp_id)
    try:
        structure = employee.salary_structure
    except SalaryStructure.DoesNotExist:
        structure = None

    if request.method == 'POST':
        def _f(key):
            try:
                return round(float(request.POST.get(key, 0) or 0), 2)
            except (ValueError, TypeError):
                return 0.0

        new_basic     = _f('basic')
        new_hra       = _f('hra')
        new_transport = _f('transport')
        new_others    = _f('others')
        new_salary    = round(new_basic + new_hra + new_transport + new_others, 2)

        effective_date = request.POST.get('effective_date')
        reason         = request.POST.get('reason', '').strip()

        old_salary    = employee.emp_salary or 0
        old_basic     = structure.basic     if structure else 0
        old_hra       = structure.hra       if structure else 0
        old_transport = structure.transport if structure else 0
        old_others    = structure.others    if structure else 0

        if new_salary > old_salary:
            change_type = 'Increment'
        elif new_salary < old_salary:
            change_type = 'Decrement'
        else:
            change_type = 'Adjustment'

        SalaryRevision.objects.create(
            employee=employee,
            change_type=change_type,
            effective_date=effective_date,
            old_salary=old_salary,
            old_basic=old_basic,
            old_hra=old_hra,
            old_transport=old_transport,
            old_others=old_others,
            new_salary=new_salary,
            new_basic=new_basic,
            new_hra=new_hra,
            new_transport=new_transport,
            new_others=new_others,
            reason=reason,
            changed_by=request.user,
        )

        employee.emp_salary = new_salary
        employee.save(update_fields=['emp_salary', 'updated_at'])

        if structure:
            structure.basic      = new_basic
            structure.hra        = new_hra
            structure.transport  = new_transport
            structure.others     = new_others
            structure.updated_by = request.user
            structure.save()
        else:
            SalaryStructure.objects.create(
                employee=employee, basic=new_basic, hra=new_hra,
                transport=new_transport, others=new_others,
                updated_by=request.user,
            )

        messages.success(request, f"Salary {change_type.lower()} applied for {employee.emp_name}.")
        return redirect('salary_history', emp_id=emp_id)

    return render(request, 'hr_de/salary/revision_form.html', {
        'employee':  employee,
        'structure': structure,
        'today':     timezone.now().date().isoformat(),
    })


@login_required
def salary_history(request, emp_id):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    employee  = get_object_or_404(Employee, pk=emp_id)
    revisions = employee.salary_revisions.select_related('changed_by').order_by('-effective_date', '-changed_at')

    return render(request, 'hr_de/salary/history.html', {
        'employee':  employee,
        'revisions': revisions,
    })


@login_required
def salary_all_revisions(request):
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    qs = SalaryRevision.objects.select_related(
        'employee', 'employee__department', 'changed_by'
    ).order_by('-effective_date', '-changed_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(employee__emp_name__icontains=q) | Q(employee__emp_id__icontains=q)
        )

    return render(request, 'hr_de/salary/all_revisions.html', {
        'revisions': qs,
        'q': q,
    })


# ── ATTENDANCE ───────────────────────────────────────────────────────────────

_ATT_STATUSES = {'present', 'absent', 'half_day', 'leave', 'holiday', 'week_off'}


def _employee_for_user(user):
    """Return the Employee linked to this login, or None."""
    try:
        return user.employee
    except Employee.DoesNotExist:
        return None


@login_required
def attendance_mark(request):
    """Employee self-service: one-tap check-in stamping the current time — TODAY only."""
    employee = _employee_for_user(request.user)
    today    = timezone.localdate()

    if request.method == 'POST':
        if employee is None:
            messages.error(request, "Your login is not linked to an employee profile.")
            return redirect('attendance_mark')
        existing = Attendance.objects.filter(employee=employee, date=today).first()
        if existing:
            messages.info(request, "You've already checked in for today.")
        else:
            now_time = timezone.localtime().time()
            Attendance.objects.create(
                employee=employee, date=today, status='present',
                check_in=now_time, source='self', marked_by=request.user,
            )
            messages.success(request, f"Checked in at {now_time.strftime('%I:%M %p')}. Have a great day!")
        return redirect('attendance_mark')

    todays = None
    recent = []
    if employee is not None:
        todays = Attendance.objects.filter(employee=employee, date=today).first()
        recent = list(
            Attendance.objects.filter(employee=employee)
            .select_related('leave_type')
            .order_by('-date')[:14]
        )

    return render(request, 'hr_de/attendance/mark.html', {
        'employee': employee,
        'today':    today,
        'todays':   todays,
        'recent':   recent,
        'now':      timezone.localtime(),
    })


@login_required
def attendance_grid(request):
    """HR month grid — department-wise, editable, with an approved-leave overlay."""
    if not _hr_only(request):
        return render(request, 'hr_de/unauthorized.html', status=403)

    import calendar
    import datetime as dt
    from collections import OrderedDict

    today = timezone.localdate()
    try:
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        month = today.month
    try:
        year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        year = today.year
    if not (1 <= month <= 12):
        month = today.month

    num_days  = calendar.monthrange(year, month)[1]
    first_day = dt.date(year, month, 1)
    last_day  = dt.date(year, month, num_days)

    # Day-header meta (Sunday → weekly off)
    day_meta = []
    for d in range(1, num_days + 1):
        dobj = dt.date(year, month, d)
        day_meta.append({
            'day':       d,
            'weekday':   dobj.strftime('%a'),
            'is_off':    dobj.weekday() == 6,
            'is_future': dobj > today,
            'is_today':  dobj == today,
        })

    # Employees (optionally filtered by department)
    dept_id   = request.GET.get('department', '').strip()
    employees = (
        Employee.objects.filter(is_active=True)
        .select_related('department')
        .order_by('department__name', 'emp_name')
    )
    if dept_id:
        employees = employees.filter(department_id=dept_id)
    employees = list(employees)
    emp_ids   = [e.id for e in employees]

    # Explicit attendance records for the month
    att_map = {}
    for a in Attendance.objects.filter(
        employee_id__in=emp_ids, date__range=(first_day, last_day)
    ).select_related('leave_type'):
        att_map[(a.employee_id, a.date.day)] = a

    # Approved-leave overlay (fills only cells without an explicit record)
    leave_map = {}
    for lv in Leave.objects.filter(
        employee_id__in=emp_ids, status='Approved'
    ).select_related('leave_type'):
        f = lv.actual_from or lv.expected_from
        t = lv.actual_to or lv.expected_to
        if not f or not t:
            continue
        cur = max(f, first_day)
        end = min(t, last_day)
        while cur <= end:
            leave_map.setdefault(
                (lv.employee_id, cur.day),
                lv.leave_type.name if lv.leave_type else 'Leave',
            )
            cur += dt.timedelta(days=1)

    # Build rows grouped by department
    grouped = OrderedDict()
    for emp in employees:
        cells = []
        present_days = leave_days = absent_days = 0
        for dm in day_meta:
            d = dm['day']
            a = att_map.get((emp.id, d))
            if a:
                status, source, check_in = a.status, a.source, a.check_in
                lt = a.leave_type.name if a.leave_type else ''
            elif (emp.id, d) in leave_map:
                status, source, check_in = 'leave', 'leave_auto', None
                lt = leave_map[(emp.id, d)]
            elif dm['is_off']:
                status, source, check_in, lt = 'week_off', 'auto', None, ''
            else:
                status, source, check_in, lt = '', '', None, ''

            if   status == 'present': present_days += 1
            elif status == 'leave':   leave_days   += 1
            elif status == 'absent':  absent_days  += 1

            cells.append({
                'day':        d,
                'status':     status,
                'leave_type': lt,
                'source':     source,
                'is_off':     dm['is_off'],
                'is_future':  dm['is_future'],
                'is_today':   dm['is_today'],
                'check_in':   check_in,
            })

        dept_name = emp.department.name if emp.department else 'Unassigned'
        grouped.setdefault(dept_name, []).append({
            'employee':     emp,
            'cells':        cells,
            'present_days': present_days,
            'leave_days':   leave_days,
            'absent_days':  absent_days,
        })

    dept_groups = [{'name': name, 'rows': rows} for name, rows in grouped.items()]

    months = [{'num': i, 'name': dt.date(2000, i, 1).strftime('%B')} for i in range(1, 13)]
    years  = list(range(today.year - 3, today.year + 2))

    return render(request, 'hr_de/attendance/grid.html', {
        'dept_groups':   dept_groups,
        'day_meta':      day_meta,
        'num_days':      num_days,
        'month':         month,
        'year':          year,
        'months':        months,
        'years':         years,
        'leave_types':   list(LeaveType.objects.all().order_by('name')),
        'departments':   Department.objects.all().order_by('name'),
        'selected_dept': dept_id,
        'today':         today,
    })


@require_POST
def attendance_cell_update(request):
    """AJAX upsert for a single grid cell (HR only)."""
    if not _hr_only(request):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    import json
    import datetime as dt

    try:
        payload = json.loads(request.body.decode('utf-8'))
        emp_id          = int(payload['employee_id'])
        year            = int(payload['year'])
        month           = int(payload['month'])
        day             = int(payload['day'])
        status          = (payload.get('status') or '').strip()
        leave_type_name = (payload.get('leave_type') or '').strip()
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid request data.'}, status=400)

    if status and status not in _ATT_STATUSES:
        return JsonResponse({'status': 'error', 'message': 'Invalid status.'}, status=400)

    try:
        date = dt.date(year, month, day)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid date.'}, status=400)

    employee = get_object_or_404(Employee, pk=emp_id)

    # Empty status clears the cell (reverts to auto / blank)
    if not status:
        Attendance.objects.filter(employee=employee, date=date).delete()
        return JsonResponse({'status': 'success', 'cleared': True})

    leave_type = None
    if status == 'leave':
        if not leave_type_name:
            return JsonResponse({'status': 'error', 'message': 'Pick a leave type.'}, status=400)
        leave_type = LeaveType.objects.filter(name=leave_type_name).first()
        if leave_type is None:
            return JsonResponse({'status': 'error', 'message': 'Unknown leave type.'}, status=400)

    att, created = Attendance.objects.update_or_create(
        employee=employee, date=date,
        defaults={
            'status':     status,
            'leave_type': leave_type,
            'source':     'hr',
            'marked_by':  request.user,
        },
    )
    return JsonResponse({
        'status':      'success',
        'created':     created,
        'cell_status': att.status,
        'leave_type':  leave_type.name if leave_type else '',
    })


@require_POST
def attendance_bulk_update(request):
    """AJAX fill: apply one status to many days of a single employee (HR only)."""
    if not _hr_only(request):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    import json
    import datetime as dt

    try:
        payload = json.loads(request.body.decode('utf-8'))
        emp_id          = int(payload['employee_id'])
        year            = int(payload['year'])
        month           = int(payload['month'])
        days            = [int(d) for d in payload['days']]
        status          = (payload.get('status') or '').strip()
        leave_type_name = (payload.get('leave_type') or '').strip()
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid request data.'}, status=400)

    if status and status not in _ATT_STATUSES:
        return JsonResponse({'status': 'error', 'message': 'Invalid status.'}, status=400)

    employee = get_object_or_404(Employee, pk=emp_id)

    leave_type = None
    if status == 'leave':
        if not leave_type_name:
            return JsonResponse({'status': 'error', 'message': 'Pick a leave type.'}, status=400)
        leave_type = LeaveType.objects.filter(name=leave_type_name).first()
        if leave_type is None:
            return JsonResponse({'status': 'error', 'message': 'Unknown leave type.'}, status=400)

    applied = []
    for d in days:
        try:
            date = dt.date(year, month, d)
        except ValueError:
            continue
        if not status:
            Attendance.objects.filter(employee=employee, date=date).delete()
        else:
            Attendance.objects.update_or_create(
                employee=employee, date=date,
                defaults={
                    'status':     status,
                    'leave_type': leave_type,
                    'source':     'hr',
                    'marked_by':  request.user,
                },
            )
        applied.append(d)

    return JsonResponse({'status': 'success', 'applied': applied})


@require_POST
def attendance_day_update(request):
    """AJAX: apply one status to many employees on a single date (e.g. a public holiday)."""
    if not _hr_only(request):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    import json
    import datetime as dt

    try:
        payload = json.loads(request.body.decode('utf-8'))
        emp_ids         = [int(x) for x in payload['employee_ids']]
        year            = int(payload['year'])
        month           = int(payload['month'])
        day             = int(payload['day'])
        status          = (payload.get('status') or '').strip()
        leave_type_name = (payload.get('leave_type') or '').strip()
    except (KeyError, ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid request data.'}, status=400)

    if status and status not in _ATT_STATUSES:
        return JsonResponse({'status': 'error', 'message': 'Invalid status.'}, status=400)

    try:
        date = dt.date(year, month, day)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid date.'}, status=400)

    leave_type = None
    if status == 'leave':
        if not leave_type_name:
            return JsonResponse({'status': 'error', 'message': 'Pick a leave type.'}, status=400)
        leave_type = LeaveType.objects.filter(name=leave_type_name).first()
        if leave_type is None:
            return JsonResponse({'status': 'error', 'message': 'Unknown leave type.'}, status=400)

    applied = 0
    for emp in Employee.objects.filter(id__in=emp_ids):
        if not status:
            Attendance.objects.filter(employee=emp, date=date).delete()
        else:
            Attendance.objects.update_or_create(
                employee=emp, date=date,
                defaults={
                    'status':     status,
                    'leave_type': leave_type,
                    'source':     'hr',
                    'marked_by':  request.user,
                },
            )
        applied += 1

    return JsonResponse({'status': 'success', 'applied': applied})
