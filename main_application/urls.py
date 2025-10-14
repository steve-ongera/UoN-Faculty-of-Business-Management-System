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
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
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

]