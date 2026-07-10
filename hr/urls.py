from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('employee/home/', views.employee_home, name='employee_home'),
    path('org-chart/', views.org_chart, name='org_chart'),
    path('org-chart/assign-head/', views.assign_head, name='assign_head'),
    path('settings/', views.settings, name='settings'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    path('employees/', views.employee_list, name='employee_list'),
    path('birthdays/', views.birthdays, name='birthdays'),
    path('birthdays/wish/', views.birthday_wish_send, name='birthday_wish_send'),
    path('birthdays/wish-log/', views.birthday_wish_log, name='birthday_wish_log'),
    path('employee/add/', views.employee_create, name='employee_create'),
    path('employee/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employee/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('my-profile/photo/', views.upload_my_photo, name='upload_my_photo'),
    path("employee-upload/", views.bulk_upload_employees, name="employee_upload"),
    path("employee-upload/template/", views.download_employee_template, name="employee_upload_template"),

    # Advance Salary
    path('advance-salary/',                     views.advance_list,    name='advance_list'),
    path('advance-salary/apply/',               views.advance_apply,   name='advance_apply'),
    path('advance-salary/pending/',             views.advance_pending, name='advance_pending'),
    path('advance-salary/<int:pk>/approve/',    views.advance_approve, name='advance_approve'),
    path('advance-salary/<int:pk>/deduction/',  views.advance_edit_deduction, name='advance_edit_deduction'),
    path('my-advances/',                        views.my_advances,     name='my_advances'),

    # Passport Requests
    path('passport-requests/',                  views.passport_list,          name='passport_list'),
    path('passport-requests/apply/',            views.passport_apply,         name='passport_apply'),
    path('passport-requests/pending/',          views.passport_pending,       name='passport_pending'),
    path('passport-requests/outstanding/',      views.passport_outstanding,   name='passport_outstanding'),
    path('passport-requests/employee/<int:emp_pk>/return/', views.passport_employee_return, name='passport_employee_return'),
    path('passport-requests/<int:pk>/approve/', views.passport_approve,       name='passport_approve'),
    path('passport-requests/<int:pk>/return/',  views.passport_mark_returned, name='passport_mark_returned'),
    path('my-passport-requests/',               views.my_passport_requests,   name='my_passport_requests'),

    ############  AUTHENTICATION URLs ############
    path('signupjunaid6231/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # HR: view the module as a specific employee ("login as employee")
    path('employee/<int:pk>/impersonate/', views.impersonate_employee, name='impersonate_employee'),
    path('stop-impersonating/', views.stop_impersonating, name='stop_impersonating'),

    path('forgot-password/', views.forgot_password, name='forgot_password'),

    path('mols/', views.mol_list, name='mol_list'),
    path('mol/add/', views.mol_add, name='mol_add'),
    path('mol/<int:pk>/edit/', views.mol_edit, name='mol_edit'),
    path('mol/<int:pk>/delete/', views.mol_delete, name='mol_delete'),

    path('md-accounts/', views.md_account_list, name='md_account_list'),
    path('md-accounts/create/', views.md_account_create, name='md_account_create'),
    path('md-accounts/<int:pk>/delete/', views.md_account_delete, name='md_account_delete'),

    path('departments/', views.department_list, name='department_list'),
    path('department/add/', views.department_add, name='department_add'),
    path('department/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('department/<int:pk>/delete/', views.department_delete, name='department_delete'),

    ### Leave Type Management URLs
    path('leave_types/', views.leave_type_list, name='leave_type_list'),
    path('leave_type/add/', views.leave_type_create, name='leave_type_create'),
    path('leave_type/<int:pk>/edit/', views.leave_type_edit, name='leave_type_edit'),
    path('leave_type/<int:pk>/delete/', views.leave_type_delete, name='leave_type_delete'),


    ### Leave Management URLs

    path('leaves/add/', views.add_leave, name='add_leave'),
    path('leaves/history/', views.leave_history, name='leave_history'),
    path('employee/<int:pk>/leaves/', views.employee_leave_detail, name='employee_leave_detail'),
    path('leaves/<int:pk>/edit/', views.leave_edit, name='edit_leave'),

    path('leaves/pending/', views.pending_leaves, name='pending_leaves'),
    path('leaves/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),

    # Employee self-service
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('my-leaves/', views.my_leaves, name='my_leaves'),
    path('my-leaves/apply/', views.submit_my_leave, name='submit_my_leave'),

    # Attendance
    path('attendance/mark/',        views.attendance_mark,        name='attendance_mark'),
    path('attendance/team/',        views.attendance_team,        name='attendance_team'),
    path('attendance/team-mark/',   views.attendance_team_mark,   name='attendance_team_mark'),
    path('attendance/grid/',        views.attendance_grid,        name='attendance_grid'),
    path('attendance/cell-update/', views.attendance_cell_update, name='attendance_cell_update'),
    path('attendance/bulk-update/', views.attendance_bulk_update, name='attendance_bulk_update'),
    path('attendance/day-update/',  views.attendance_day_update,  name='attendance_day_update'),

    # HR: salary structure per employee
    path('employee/<int:emp_pk>/salary-structure/', views.salary_structure, name='salary_structure'),

    # HR: salary revision (audit trail)
    path('employee/<int:emp_id>/salary/revise/',  views.salary_revision_create, name='salary_revision_create'),
    path('employee/<int:emp_id>/salary/history/', views.salary_history,          name='salary_history'),
    path('salary-changes/',                        views.salary_all_revisions,   name='salary_all_revisions'),

    # Payroll (HR only)
    path('payroll/',                                views.payroll_list,          name='payroll_list'),
    path('payroll/create/',                         views.payroll_create,        name='payroll_create'),
    path('payroll/<int:pk>/',                       views.payroll_detail,        name='payroll_detail'),
    path('payroll/<int:pk>/confirm/',               views.payroll_confirm,       name='payroll_confirm'),
    path('payroll/<int:pk>/delete/',                views.payroll_delete,        name='payroll_delete'),
    path('payroll/<int:pk>/wps-export/',            views.payroll_wps_export,    name='payroll_wps_export'),
    path('payroll/entry/<int:entry_pk>/edit/',      views.payroll_entry_update,  name='payroll_entry_update'),
    path('payroll/entry/<int:entry_pk>/remove/',    views.payroll_entry_remove,  name='payroll_entry_remove'),
    path('payroll/entry/<int:entry_pk>/payslip/',   views.payslip,               name='payslip'),

    # Head: apply leave on behalf of any dept employee
    path('employee/<int:emp_pk>/apply-leave/', views.apply_leave_behalf, name='apply_leave_behalf'),
    # Head: set/update actual rejoining date
    path('leave/<int:leave_pk>/set-rejoining/', views.set_rejoining_date, name='set_rejoining_date'),

    # Reviews (Head fills weekly + monthly; HR/MD read)
    path('reviews/team/',                  views.review_team,     name='review_team'),
    path('reviews/edit/<int:emp_pk>/',     views.review_edit,     name='review_edit'),
    path('reviews/overview/',              views.review_overview, name='review_overview'),
    path('reviews/employee/<int:emp_pk>/', views.review_employee, name='review_employee'),

    # Other Records (document store — HR & MD only)
    path('other-records/',                 views.other_records_list,  name='other_records_list'),
    path('other-records/add/',             views.other_record_add,    name='other_record_add'),
    path('other-records/<int:pk>/edit/',   views.other_record_edit,   name='other_record_edit'),
    path('other-records/<int:pk>/delete/', views.other_record_delete, name='other_record_delete'),

    # Vehicle Management (fleet register — HR & MD only)
    path('vehicles/',                 views.vehicle_list,   name='vehicle_list'),
    path('vehicles/add/',             views.vehicle_add,    name='vehicle_add'),
    path('vehicles/upload/',          views.vehicle_bulk_upload,    name='vehicle_upload'),
    path('vehicles/upload/template/', views.vehicle_upload_template, name='vehicle_upload_template'),
    path('vehicles/<int:pk>/',        views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<int:pk>/edit/',   views.vehicle_edit,   name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),

    # Vehicle Services (maintenance history + employee requests)
    path('vehicles/<int:pk>/services/',      views.vehicle_services,     name='vehicle_services'),
    path('vehicles/<int:pk>/services/add/',  views.vehicle_service_add,  name='vehicle_service_add'),
    path('vehicle-services/requests/',       views.vehicle_service_requests, name='vehicle_service_requests'),
    path('vehicle-services/<int:pk>/process/', views.vehicle_service_process, name='vehicle_service_process'),
    path('vehicle-services/<int:pk>/delete/',  views.vehicle_service_delete,  name='vehicle_service_delete'),

    # Management Details (owners/directors + families — HR & MD only)
    path('management/',                          views.management_list,       name='management_list'),
    path('management/add/',                      views.management_add,        name='management_add'),
    path('management/<int:pk>/',                 views.management_detail,     name='management_detail'),
    path('management/<int:pk>/edit/',            views.management_edit,       name='management_edit'),
    path('management/<int:pk>/delete/',          views.management_delete,     name='management_delete'),
    path('management/<int:head_pk>/family/add/', views.management_family_add, name='management_family_add'),
    path('management/<int:member_pk>/travel/add/', views.travel_add,          name='travel_add'),
    path('management-travel/<int:pk>/delete/',   views.travel_delete,         name='travel_delete'),
    path('management/<int:member_pk>/visa/add/', views.country_visa_add,      name='country_visa_add'),
    path('management-visa/<int:pk>/delete/',     views.country_visa_delete,   name='country_visa_delete'),

    # Memos (official memorandums — HR & MD only)
    path('memos/',               views.memo_list,   name='memo_list'),
    path('memos/add/',           views.memo_add,    name='memo_add'),
    path('memos/<int:pk>/edit/', views.memo_edit,   name='memo_edit'),
    path('memos/<int:pk>/pdf/',  views.memo_pdf,    name='memo_pdf'),
    path('memos/<int:pk>/delete/', views.memo_delete, name='memo_delete'),

    # Company Properties (assets assignable to employees — HR & MD only)
    path('properties/',              views.property_list,   name='property_list'),
    path('properties/add/',          views.property_add,    name='property_add'),
    path('properties/<int:pk>/edit/',   views.property_edit,   name='property_edit'),
    path('properties/<int:pk>/delete/', views.property_delete, name='property_delete'),

    # Employee self-service: my vehicles + request service
    path('my-vehicles/',                     views.my_vehicles,          name='my_vehicles'),
    path('my-vehicles/<int:pk>/request-service/', views.request_vehicle_service, name='request_vehicle_service'),
    path('my-vehicle-services/<int:pk>/complete/', views.complete_vehicle_service, name='complete_vehicle_service'),






]