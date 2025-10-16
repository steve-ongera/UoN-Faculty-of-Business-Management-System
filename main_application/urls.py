from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard URLs
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('dashboard/cod/', views.cod_dashboard, name='cod_dashboard'),
    path('dashboard/dean/', views.dean_dashboard, name='dean_dashboard'),
    path('dashboard/admin-', views.admin_dashboard, name='admin_dashboard'),
    path('student_announcements_list/', views.student_announcements_list, name='student_announcements_list'),
    path('student_announcement_detail/announcement/<int:pk>/', views.student_announcement_detail, name='student_announcement_detail'),

    # Events URLs
    path('events/', views.student_events_list, name='student_events_list'),
    path('events/<int:event_id>/', views.student_event_detail, name='student_event_detail'),
    path('events/<int:event_id>/register/', views.register_for_event, name='register_for_event'),
    path('events/<int:event_id>/unregister/', views.unregister_from_event, name='unregister_from_event'),

    path('units/register/', views.register_units, name='register_units'),
    path('units/enrollments/', views.student_enrollments, name='student_enrollments'),
    path('units/<int:enrollment_id>/drop/', views.drop_unit, name='drop_unit'),
    path('my_programme/', views.my_programme, name='my_programme'),
    path('profile/', views.student_profile_view, name='student_profile'),
    path('semester-reporting/', views.student_semester_reporting, name='student_semester_reporting'),
    path('academic-calendar/', views.student_academic_calendar, name='student_academic_calendar'),
    path('timetable/', views.student_timetable_view, name='student_timetable'),

    path('messages/', views.messaging_list, name='messaging_list'),
    path('messages/<int:user_id>/', views.message_thread, name='message_thread'),
    path('api/messages/send/<int:user_id>/', views.send_message, name='send_message'),
    path('api/messages/search/', views.search_users, name='search_users'),
    path('api/messages/mark-read/<int:message_id>/', views.mark_as_read, name='mark_as_read'),
    path('api/messages/unread-count/', views.get_unread_count, name='get_unread_count'),
    path('api/messages/delete/<int:user_id>/', views.delete_conversation, name='delete_conversation'),

    path('student_grades_view/', views.student_grades_view, name='student_grades_view'),
    path('academic_performance_view/', views.academic_performance_view, name='academic_performance_view'),


    path('marks-entry/', views.marks_entry_view, name='marks_entry_view'),
    path('search-student/', views.search_student_ajax, name='search_student_ajax'),
    path('student/<int:student_id>/semester/<int:semester_id>/', views.student_units_view, name='student_units_view'),
    path('save-marks/', views.save_marks_ajax, name='save_marks_ajax'),
    path('calculate-final-grade/', views.calculate_final_grade_ajax, name='calculate_final_grade_ajax'),
    path('bulk-entry/semester/<int:semester_id>/unit/<int:unit_id>/',views.bulk_marks_entry_view, name='bulk_marks_entry_view'),

    # Student Management URLs
    path('admin-students/', views.student_list, name='student_list'),
    path('admin-students/create/', views.student_create, name='student_create'),
    path('admin-students/<str:registration_number>/', views.student_detail, name='student_detail'),
    path('admin-students/<str:registration_number>/update/', views.student_update, name='student_update'),
    path('admin-students/<str:registration_number>/delete/', views.student_delete, name='student_delete'),
    path('admin-students/export/csv/', views.student_export, name='student_export'),

    # Lecturer Management URLs
    path('admin-lecturers/', views.lecturer_list, name='lecturer_list'),
    path('admin-lecturers/create/', views.lecturer_create, name='lecturer_create'),
    path('admin-lecturers/<str:staff_number>/', views.lecturer_detail, name='lecturer_detail'),
    path('admin-lecturers/<str:staff_number>/update/', views.lecturer_update, name='lecturer_update'),
    path('admin-lecturers/<str:staff_number>/delete/', views.lecturer_delete, name='lecturer_delete'),
    path('admin-lecturers/export/csv/', views.lecturer_export, name='lecturer_export'),

    # Programme Management
    path('programmes/', views.programme_list, name='programme_list'),
    path('programme/create/', views.programme_create, name='programme_create'),
    path('programme/<str:programme_code>/', views.programme_detail, name='programme_detail'),
    path('programme/<str:programme_code>/update/', views.programme_update, name='programme_update'),
    path('programme/<str:programme_code>/delete/', views.programme_delete, name='programme_delete'),
    path('programme/<str:programme_code>/export/', views.programme_export_structure, name='programme_export_structure'),

    # AJAX Endpoints
    path('programme/<str:programme_code>/add-unit/', views.programme_add_unit, name='programme_add_unit'),
    path('programme/unit/<int:programme_unit_id>/update/', views.programme_update_unit, name='programme_update_unit'),
    path('programme/unit/<int:programme_unit_id>/delete/', views.programme_delete_unit, name='programme_delete_unit'),

    # Announcement URLs
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/update/', views.announcement_update, name='announcement_update'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    
    # Event URLs
    path('admin-events/', views.event_list, name='event_list'),
    path('admin-events/<int:pk>/', views.event_detail, name='event_detail'),
    path('admin-events/create/', views.event_create, name='event_create'),
    path('admin-events/<int:pk>/update/', views.event_update, name='event_update'),
    path('admin-events/<int:pk>/delete/', views.event_delete, name='event_delete'),

]