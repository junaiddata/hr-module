"""Standalone PDF builders shared between views (download/print) and the
WhatsApp sender (attaching the same document to the outbound message).

Kept dependency-free of `views`/`whatsapp` so either can import this module
without risking a circular import.
"""
import os
import html as _html
from io import BytesIO

from django.conf import settings
from django.utils import timezone


def build_labour_renewal_pdf(prompt):
    """Render the 'Employment Terms Renewal' consent letter for a
    LabourCardRenewalPrompt and return the PDF as raw bytes.

    `prompt` needs `.pk`, `.created_at`, `.expiry_snapshot`, `.response`,
    `.response_raw`, and `.employee` (with `.emp_name`, `.emp_id`,
    `.department`, `.mol`) populated — select_related them before calling.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from PIL import Image as PILImage

    employee = prompt.employee

    PW, _PH = A4
    margin = 22 * mm
    content_w = PW - 2 * margin

    buf = BytesIO()

    # Crop the company logo strip out of the shared letterhead JPG so a
    # second static asset isn't needed just for this letter.
    logo_flowable = None
    letterhead_path = os.path.join(settings.MEDIA_ROOT, 'HR MEMO SAMPLE.JPG')
    if os.path.exists(letterhead_path):
        with PILImage.open(letterhead_path) as im:
            logo_crop = im.crop((0, 0, im.width, 230))
            logo_buf = BytesIO()
            logo_crop.convert('RGB').save(logo_buf, format='PNG')
            logo_buf.seek(0)
        logo_flowable = RLImage(logo_buf, width=content_w, height=content_w * 230 / im.width)

    label_style = ParagraphStyle('lr_label', fontName='Helvetica-Bold', fontSize=10, leading=13)
    value_style = ParagraphStyle('lr_value', fontName='Helvetica-Bold', fontSize=10, leading=13)
    body_style  = ParagraphStyle('lr_body',  fontName='Helvetica', fontSize=10.5, leading=16)
    small_style = ParagraphStyle('lr_small', fontName='Helvetica', fontSize=10, leading=14)

    ref_no      = f"JN/HR-VISARENEWAL/{prompt.created_at.strftime('%d%m%Y')}-{prompt.pk}"
    dept_name   = employee.department.name if employee.department else '—'
    mol_name    = employee.mol.mol if employee.mol else '—'
    expiry_str  = prompt.expiry_snapshot.strftime('%d %b %Y')
    letter_date = timezone.now().strftime('%d %b %Y')

    info_rows = [
        [Paragraph('REF:', label_style),        Paragraph(_html.escape(ref_no), value_style)],
        [Paragraph('DATE:', label_style),       Paragraph(letter_date, value_style)],
        ['', ''],
        [Paragraph('To', label_style),          Paragraph(_html.escape(employee.emp_name.upper()), value_style)],
        [Paragraph('EMP ID', label_style),      Paragraph(_html.escape(employee.emp_id), value_style)],
        [Paragraph('DEPARTMENT', label_style),  Paragraph(_html.escape(dept_name.upper()), value_style)],
        [Paragraph('MOL', label_style),         Paragraph(_html.escape(mol_name.upper()), value_style)],
    ]
    info_table = Table(info_rows, colWidths=[35 * mm, content_w - 35 * mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))

    subject_data = [
        [Paragraph('SUBJECT', label_style), Paragraph('EMPLOYMENT TERMS RENEWAL', value_style), ''],
        ['', Paragraph('Residence Visa', value_style), Paragraph(expiry_str, value_style)],
    ]
    subject_table = Table(subject_data, colWidths=[30 * mm, 70 * mm, content_w - 100 * mm])
    subject_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (2, 0)),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))

    yes_mark = 'X' if prompt.response == 'Yes' else ' '
    no_mark  = 'X' if prompt.response == 'No' else ' '
    tick_table = Table([[
        Paragraph(f'( {yes_mark} ) Yes, renew my work permit', small_style),
        Paragraph(f'( {no_mark} ) No, do not renew my work permit', small_style),
    ]], colWidths=[content_w / 2, content_w / 2])
    tick_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))

    reason_line = Table([['']], colWidths=[content_w])
    reason_line.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey)]))

    sig_table = Table(
        [['', ''], [Paragraph('Employee Signature', label_style), Paragraph('Approval of HOD', label_style)]],
        colWidths=[content_w / 2, content_w / 2], rowHeights=[34, 16],
    )
    sig_table.setStyle(TableStyle([('LINEABOVE', (0, 1), (-1, 1), 0.75, colors.black)]))

    reason_text = _html.escape(prompt.response_raw) if (prompt.response == 'No' and prompt.response_raw) else ''

    story = []
    if logo_flowable:
        story += [logo_flowable, Spacer(1, 10)]
    story += [
        info_table, Spacer(1, 10),
        subject_table, Spacer(1, 16),
        Paragraph(f'Dear {_html.escape(employee.emp_name.upper())},', body_style),
        Spacer(1, 8),
        Paragraph(
            'We are pleased to inform you that your Labour Contract &amp; Residence Visa is due for the '
            'renewal as mentioned above. Please mark your consent to proceed further in the columns below;',
            body_style,
        ),
        Spacer(1, 14),
        Paragraph('<b>Please tick Yes or No:</b>', body_style),
        Spacer(1, 10),
        tick_table, Spacer(1, 16),
        Paragraph(f'<b>Reason:</b> {reason_text}', body_style),
        Spacer(1, 4),
        reason_line, Spacer(1, 22),
        Paragraph('Kindly sign on the space provided below in acknowledgement.', body_style),
        Spacer(1, 30),
        sig_table,
    ]

    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=margin, rightMargin=margin,
                            topMargin=margin, bottomMargin=margin)
    doc.build(story)
    buf.seek(0)
    return buf.read()
