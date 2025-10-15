from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from .models import *


@csrf_protect
@never_cache
def login_view(request):
    """
    Unified login view for all user types.
    Redirects to appropriate dashboard based on user_type.
    """
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active and user.is_active_user:
                # Log the user in
                login(request, user)
                
                # Set session expiry
                if not remember:
                    request.session.set_expiry(0)  # Browser close
                else:
                    request.session.set_expiry(1209600)  # 2 weeks
                
                # Success message
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to appropriate dashboard
                return redirect_to_dashboard(user)
            else:
                messages.error(request, 'Your account has been deactivated. Please contact the administrator.')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
    
    return render(request, 'authentication/login.html')


def redirect_to_dashboard(user):
    """
    Redirect user to appropriate dashboard based on user_type.
    """
    user_type = user.user_type
    
    dashboard_urls = {
        'STUDENT': 'student_dashboard',
        'LECTURER': 'lecturer_dashboard',
        'COD': 'cod_dashboard',
        'DEAN': 'dean_dashboard',
        'ICT_ADMIN': 'admin_dashboard',
    }
    
    # If superuser, redirect to admin dashboard
    if user.is_superuser or user.is_staff:
        return redirect('admin_dashboard')
    
    # Get the appropriate dashboard URL
    dashboard_url = dashboard_urls.get(user_type, 'admin_dashboard')
    
    return redirect(dashboard_url)


@login_required
def logout_view(request):
    """
    Logout view for all users.
    """
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('login')


# ========================
# DASHBOARD VIEWS
# ========================

@login_required
def student_dashboard(request):
    """
    Dashboard for students.
    """
    if request.user.user_type != 'STUDENT':
        messages.error(request, 'Access denied. You do not have permission to view this page.')
        return redirect_to_dashboard(request.user)
    
    try:
        student = request.user.student_profile
        
        # Get student data
        context = {
            'student': student,
            'current_semester': get_current_semester(),
            'enrolled_units': get_student_enrolled_units(student),
            'upcoming_classes': get_student_timetable(student),
            'recent_announcements': get_student_announcements(student),
            'fee_balance': get_student_fee_balance(student),
            'academic_performance': get_student_performance(student),
        }
        
        return render(request, 'dashboards/student_dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('login')


@login_required
def lecturer_dashboard(request):
    """
    Dashboard for lecturers.
    """
    if request.user.user_type != 'LECTURER':
        messages.error(request, 'Access denied. You do not have permission to view this page.')
        return redirect_to_dashboard(request.user)
    
    try:
        lecturer = request.user.lecturer_profile
        
        # Get lecturer data
        context = {
            'lecturer': lecturer,
            'current_semester': get_current_semester(),
            'allocated_units': get_lecturer_units(lecturer),
            'today_classes': get_lecturer_today_classes(lecturer),
            'pending_marks': get_pending_marks_count(lecturer),
            'student_count': get_lecturer_student_count(lecturer),
            'recent_announcements': get_general_announcements(),
        }
        
        return render(request, 'dashboards/lecturer_dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('login')


@login_required
def cod_dashboard(request):
    """
    Dashboard for Chairman of Department (COD).
    """
    if request.user.user_type != 'COD':
        messages.error(request, 'Access denied. You do not have permission to view this page.')
        return redirect_to_dashboard(request.user)
    
    try:
        # Get COD's department
        departments = request.user.headed_departments.all()
        
        if not departments.exists():
            messages.warning(request, 'You are not assigned as head of any department.')
            return render(request, 'dashboards/cod_dashboard.html', {'departments': []})
        
        department = departments.first()
        
        # Get department data
        context = {
            'department': department,
            'current_semester': get_current_semester(),
            'total_students': get_department_students_count(department),
            'total_lecturers': get_department_lecturers_count(department),
            'total_programmes': get_department_programmes_count(department),
            'pending_approvals': get_pending_grade_approvals(department),
            'recent_announcements': get_general_announcements(),
        }
        
        return render(request, 'dashboards/cod_dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('login')


@login_required
def dean_dashboard(request):
    """
    Dashboard for Dean.
    """
    if request.user.user_type != 'DEAN':
        messages.error(request, 'Access denied. You do not have permission to view this page.')
        return redirect_to_dashboard(request.user)
    
    try:
        # Get faculty-wide data
        context = {
            'current_semester': get_current_semester(),
            'total_students': get_all_students_count(),
            'total_lecturers': get_all_lecturers_count(),
            'total_programmes': get_all_programmes_count(),
            'total_departments': get_all_departments_count(),
            'revenue_this_semester': get_semester_revenue(),
            'pending_approvals': get_all_pending_approvals(),
            'recent_events': get_upcoming_events(),
            'recent_announcements': get_general_announcements(),
        }
        
        return render(request, 'dashboards/dean_dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('login')


@login_required
def admin_dashboard(request):
    """
    Dashboard for ICT Admin and Superusers.
    """
    if request.user.user_type not in ['ICT_ADMIN'] and not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'Access denied. You do not have permission to view this page.')
        return redirect_to_dashboard(request.user)
    
    try:
        # Get system-wide statistics
        context = {
            'current_semester': get_current_semester(),
            'total_users': get_total_users(),
            'total_students': get_all_students_count(),
            'total_lecturers': get_all_lecturers_count(),
            'total_programmes': get_all_programmes_count(),
            'total_departments': get_all_departments_count(),
            'active_sessions': get_active_sessions_count(),
            'system_health': get_system_health(),
            'recent_activities': get_recent_system_activities(),
        }
        
        return render(request, 'dashboards/admin_dashboard.html', context)
    
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('login')


# ========================
# HELPER FUNCTIONS
# ========================

def get_current_semester():
    """Get the current active semester."""
    from .models import Semester
    try:
        return Semester.objects.filter(is_current=True).first()
    except:
        return None


def get_student_enrolled_units(student):
    """Get units enrolled by student in current semester."""
    from .models import UnitEnrollment
    current_semester = get_current_semester()
    if current_semester:
        return UnitEnrollment.objects.filter(
            student=student,
            semester=current_semester,
            status='ENROLLED'
        ).select_related('unit')
    return []


def get_student_timetable(student):
    """Get student's timetable for current semester."""
    from .models import TimetableSlot
    current_semester = get_current_semester()
    if current_semester:
        return TimetableSlot.objects.filter(
            programme=student.programme,
            year_level=student.current_year,
            unit_allocation__semester=current_semester,
            is_active=True
        ).select_related('unit_allocation__unit', 'venue').order_by('day_of_week', 'start_time')[:5]
    return []


def get_student_announcements(student):
    """Get announcements relevant to student."""
    from .models import Announcement
    from django.utils import timezone
    return Announcement.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).filter(
        target_programmes=student.programme
    ).order_by('-publish_date')[:5]


def get_student_fee_balance(student):
    """Get student's fee balance."""
    from .models import FeeStatement
    current_semester = get_current_semester()
    if current_semester:
        try:
            statement = FeeStatement.objects.get(student=student, semester=current_semester)
            return {
                'total_billed': statement.total_billed,
                'total_paid': statement.total_paid,
                'balance': statement.balance,
                'can_register': statement.can_register
            }
        except:
            return None
    return None


def get_student_performance(student):
    """Get student's academic performance summary."""
    from .models import FinalGrade
    from django.db.models import Avg, Count
    
    grades = FinalGrade.objects.filter(
        enrollment__student=student,
        is_approved=True
    )
    
    return {
        'total_units': grades.count(),
        'average_grade_point': grades.aggregate(avg=Avg('grade_point'))['avg'] or 0,
        'units_passed': grades.filter(grade__in=['A', 'B', 'C', 'D']).count(),
        'units_failed': grades.filter(grade='F').count(),
    }


def get_lecturer_units(lecturer):
    """Get units allocated to lecturer."""
    from .models import UnitAllocation
    current_semester = get_current_semester()
    if current_semester:
        return UnitAllocation.objects.filter(
            lecturer=lecturer,
            semester=current_semester,
            is_active=True
        ).select_related('unit').prefetch_related('programmes')
    return []


def get_lecturer_today_classes(lecturer):
    """Get lecturer's classes for today."""
    from .models import TimetableSlot
    from datetime import datetime
    current_semester = get_current_semester()
    today = datetime.now().strftime('%A').upper()
    
    if current_semester:
        return TimetableSlot.objects.filter(
            unit_allocation__lecturer=lecturer,
            unit_allocation__semester=current_semester,
            day_of_week=today,
            is_active=True
        ).select_related('venue', 'unit_allocation__unit').order_by('start_time')
    return []


def get_pending_marks_count(lecturer):
    """Get count of pending marks entry."""
    from .models import StudentMarks, UnitEnrollment
    current_semester = get_current_semester()
    if current_semester:
        # Get enrollments for lecturer's units
        enrollments = UnitEnrollment.objects.filter(
            unit__allocations__lecturer=lecturer,
            semester=current_semester,
            status='ENROLLED'
        ).count()
        
        # Get marks already entered
        marks_entered = StudentMarks.objects.filter(
            entered_by=lecturer,
            enrollment__semester=current_semester
        ).values('enrollment').distinct().count()
        
        return enrollments - marks_entered
    return 0


def get_lecturer_student_count(lecturer):
    """Get total students taught by lecturer."""
    from .models import UnitEnrollment
    current_semester = get_current_semester()
    if current_semester:
        return UnitEnrollment.objects.filter(
            unit__allocations__lecturer=lecturer,
            semester=current_semester,
            status='ENROLLED'
        ).values('student').distinct().count()
    return 0


def get_general_announcements():
    """Get general announcements."""
    from .models import Announcement
    from django.utils import timezone
    return Announcement.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).order_by('-publish_date')[:5]


def get_department_students_count(department):
    """Get count of students in department."""
    from .models import Student
    return Student.objects.filter(
        programme__department=department,
        is_active=True
    ).count()


def get_department_lecturers_count(department):
    """Get count of lecturers in department."""
    from .models import Lecturer
    return Lecturer.objects.filter(
        department=department,
        is_active=True
    ).count()


def get_department_programmes_count(department):
    """Get count of programmes in department."""
    from .models import Programme
    return Programme.objects.filter(
        department=department,
        is_active=True
    ).count()


def get_pending_grade_approvals(department):
    """Get pending grade approvals for department."""
    from .models import FinalGrade
    return FinalGrade.objects.filter(
        enrollment__unit__department=department,
        is_approved=False
    ).count()


def get_all_students_count():
    """Get total count of active students."""
    from .models import Student
    return Student.objects.filter(is_active=True).count()


def get_all_lecturers_count():
    """Get total count of active lecturers."""
    from .models import Lecturer
    return Lecturer.objects.filter(is_active=True).count()


def get_all_programmes_count():
    """Get total count of active programmes."""
    from .models import Programme
    return Programme.objects.filter(is_active=True).count()


def get_all_departments_count():
    """Get total count of departments."""
    from .models import Department
    return Department.objects.count()


def get_semester_revenue():
    """Get total revenue for current semester."""
    from .models import FeePayment
    from django.db.models import Sum
    current_semester = get_current_semester()
    if current_semester:
        total = FeePayment.objects.filter(
            semester=current_semester
        ).aggregate(total=Sum('amount_paid'))['total']
        return total or 0
    return 0


def get_all_pending_approvals():
    """Get all pending grade approvals."""
    from .models import FinalGrade
    return FinalGrade.objects.filter(is_approved=False).count()


def get_upcoming_events():
    """Get upcoming events."""
    from .models import Event
    from django.utils import timezone
    return Event.objects.filter(
        event_date__gte=timezone.now().date()
    ).order_by('event_date', 'start_time')[:5]


def get_total_users():
    """Get total count of users."""
    from .models import User
    return User.objects.filter(is_active=True).count()


def get_active_sessions_count():
    """Get count of active user sessions."""
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    return Session.objects.filter(expire_date__gte=timezone.now()).count()


def get_system_health():
    """Get system health metrics."""
    # This is a placeholder - implement actual health checks
    return {
        'status': 'healthy',
        'database': 'connected',
        'cache': 'active',
        'uptime': '99.9%'
    }


def get_recent_system_activities():
    """Get recent system activities."""
    # This is a placeholder - implement actual activity logging
    return []

# ========================
#student views.py
# No changes made to this file
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone


@login_required
@never_cache
def student_announcements_list(request):
    """
    List all announcements visible to the student.
    Announcements are filtered based on student's programme.
    """
    if request.user.user_type != 'STUDENT':
        return redirect('student_dashboard')
    
    try:
        student = request.user.student_profile
        
        # Get announcements for student's programme
        announcements = Announcement.objects.filter(
            is_published=True,
            publish_date__lte=timezone.now()
        ).filter(
            Q(target_programmes=student.programme) | Q(target_programmes__isnull=True)
        ).order_by('-publish_date').distinct()
        
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            announcements = announcements.filter(
                Q(title__icontains=search_query) | Q(content__icontains=search_query)
            )
        
        # Filter by priority
        priority_filter = request.GET.get('priority', '')
        if priority_filter:
            announcements = announcements.filter(priority=priority_filter)
        
        # Pagination
        paginator = Paginator(announcements, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'announcements': page_obj.object_list,
            'search_query': search_query,
            'priority_filter': priority_filter,
            'priorities': [
                ('LOW', 'Low'),
                ('NORMAL', 'Normal'),
                ('HIGH', 'High'),
                ('URGENT', 'Urgent'),
            ],
            'total_announcements': announcements.count(),
        }
        
        return render(request, 'student/announcements/announcements_list.html', context)
    
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'Error loading announcements: {str(e)}')
        return redirect('student_dashboard')


@login_required
@never_cache
def student_announcement_detail(request, pk):
    """
    Display detailed view of a single announcement.
    Only shows announcements visible to student's programme.
    """
    if request.user.user_type != 'STUDENT':
        return redirect('student_dashboard')
    
    try:
        student = request.user.student_profile
        
        # Get announcement and verify access
        announcement = get_object_or_404(
            Announcement,
            pk=pk,
            is_published=True,
            publish_date__lte=timezone.now()
        )
        
        # Check if announcement is for student's programme
        if announcement.target_programmes.exists():
            if student.programme not in announcement.target_programmes.all():
                return redirect('student_announcements_list')
        
        # Check if announcement has expired
        if announcement.expiry_date and announcement.expiry_date < timezone.now():
            from django.contrib import messages
            messages.warning(request, 'This announcement has expired.')
            return redirect('student_announcements_list')
        
        # Get related announcements (same programme)
        related_announcements = Announcement.objects.filter(
            is_published=True,
            publish_date__lte=timezone.now(),
            target_programmes=student.programme
        ).exclude(pk=pk).order_by('-publish_date')[:5]
        
        context = {
            'announcement': announcement,
            'related_announcements': related_announcements,
        }
        
        return render(request, 'student/announcements/announcement_detail.html', context)
    
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'Error loading announcement: {str(e)}')
        return redirect('student_announcements_list')



# views.py - Student Events Views
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from .models import Event, EventRegistration, Student, Programme

@login_required(login_url='login')
def student_events_list(request):
    """List all upcoming events for students"""
    # Get current student
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    # Get student's programme
    student_programme = student.programme
    
    # Base queryset - events for student's programme or general events
    events = Event.objects.filter(
        Q(target_programmes=student_programme) | Q(target_programmes__isnull=True),
        event_date__gte=timezone.now().date(),
        is_published=True
    ).distinct().order_by('event_date', 'start_time')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Filter by event type
    event_type_filter = request.GET.get('event_type', '')
    if event_type_filter:
        events = events.filter(event_type=event_type_filter)
    
    # Filter by mandatory status
    mandatory_filter = request.GET.get('mandatory', '')
    if mandatory_filter == 'true':
        events = events.filter(is_mandatory=True)
    elif mandatory_filter == 'false':
        events = events.filter(is_mandatory=False)
    
    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get registered events for current student
    registered_events = EventRegistration.objects.filter(
        student=student
    ).values_list('event_id', flat=True)
    
    # Add registration status to events
    for event in page_obj:
        event.is_registered = event.id in registered_events
        event.can_register = event.max_attendees is None or \
                           event.registrations.count() < event.max_attendees
    
    context = {
        'page_obj': page_obj,
        'events': page_obj.object_list,
        'search_query': search_query,
        'event_type_filter': event_type_filter,
        'mandatory_filter': mandatory_filter,
        'total_events': paginator.count,
        'event_type_choices': Event.EVENT_TYPES,
        'registered_events': registered_events,
    }
    
    return render(request, 'student/events/events_list.html', context)


@login_required(login_url='login')
def student_event_detail(request, event_id):
    """Display event detail and handle registration"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    event = get_object_or_404(Event, id=event_id)
    
    # Check if student is registered
    registration = EventRegistration.objects.filter(
        event=event,
        student=student
    ).first()
    
    # Check if event is full
    is_event_full = (event.max_attendees and 
                     event.registrations.count() >= event.max_attendees)
    
    # Check if registration is required but not done
    can_view = not event.registration_required or registration is not None
    
    context = {
        'event': event,
        'registration': registration,
        'is_registered': registration is not None,
        'is_event_full': is_event_full,
        'attendee_count': event.registrations.count(),
        'remaining_slots': max(0, (event.max_attendees or 0) - event.registrations.count()) if event.max_attendees else None,
        'can_view': can_view,
    }
    
    return render(request, 'student/events/event_detail.html', context)


@login_required(login_url='login')
def register_for_event(request, event_id):
    """Register student for an event"""
    if request.method != 'POST':
        return redirect('student_event_detail', event_id=event_id)
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    event = get_object_or_404(Event, id=event_id)
    
    # Check if already registered
    if EventRegistration.objects.filter(event=event, student=student).exists():
        messages.warning(request, "You are already registered for this event.")
        return redirect('student_event_detail', event_id=event_id)
    
    # Check if event is full
    if event.max_attendees and event.registrations.count() >= event.max_attendees:
        messages.error(request, "This event is full and no longer accepting registrations.")
        return redirect('student_event_detail', event_id=event_id)
    
    # Create registration
    EventRegistration.objects.create(
        event=event,
        student=student
    )
    
    messages.success(request, f"Successfully registered for {event.title}!")
    return redirect('student_event_detail', event_id=event_id)


@login_required(login_url='login')
def unregister_from_event(request, event_id):
    """Unregister student from an event"""
    if request.method != 'POST':
        return redirect('student_event_detail', event_id=event_id)
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    event = get_object_or_404(Event, id=event_id)
    
    registration = EventRegistration.objects.filter(
        event=event,
        student=student
    ).first()
    
    if registration:
        registration.delete()
        messages.success(request, f"Unregistered from {event.title}.")
    else:
        messages.warning(request, "You are not registered for this event.")
    
    return redirect('student_event_detail', event_id=event_id)

# views.py - Student Units Management Views
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.utils import timezone
from datetime import timedelta
from .models import (
    Student, Unit, ProgrammeUnit, UnitEnrollment, SemesterRegistration, 
    Semester, AcademicYear
)


@login_required(login_url='login')
def register_units(request):
    """Register units for current semester"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    # Get current semester
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        messages.error(request, "No active semester found.")
        return redirect('student_dashboard')
    
    # Check if student can register
    registration_deadline = current_semester.registration_deadline
    if timezone.now().date() > registration_deadline:
        messages.error(request, f"Registration deadline has passed ({registration_deadline}).")
        return redirect('student_dashboard')
    
    # Get available units for student's programme and year
    available_units = ProgrammeUnit.objects.filter(
        programme=student.programme,
        year_level=student.current_year,
        semester=current_semester.semester_number
    ).select_related('unit')
    
    # Get already enrolled units for this semester
    enrolled_unit_ids = UnitEnrollment.objects.filter(
        student=student,
        semester=current_semester
    ).values_list('unit_id', flat=True)
    
    # Check if semester registration exists
    sem_registration, created = SemesterRegistration.objects.get_or_create(
        student=student,
        semester=current_semester
    )
    
    if request.method == 'POST':
        selected_units = request.POST.getlist('units')
        
        if not selected_units:
            messages.warning(request, "Please select at least one unit.")
            return redirect('register_units')
        
        # Validate that selected units belong to student's programme
        valid_units = ProgrammeUnit.objects.filter(
            id__in=selected_units,
            programme=student.programme,
            year_level=student.current_year,
            semester=current_semester.semester_number
        ).values_list('unit_id', flat=True)
        
        created_count = 0
        for unit_id in valid_units:
            # Check if already enrolled
            if unit_id not in enrolled_unit_ids:
                UnitEnrollment.objects.create(
                    student=student,
                    unit_id=unit_id,
                    semester=current_semester,
                    status='ENROLLED'
                )
                created_count += 1
        
        # Update semester registration
        sem_registration.units_enrolled = UnitEnrollment.objects.filter(
            student=student,
            semester=current_semester
        ).count()
        sem_registration.status = 'REGISTERED'
        sem_registration.save()
        
        if created_count > 0:
            messages.success(request, f"Successfully registered for {created_count} unit(s).")
        else:
            messages.info(request, "Units already registered.")
        
        return redirect('student_enrollments')
    
    # Separate mandatory and elective units
    mandatory_units = available_units.filter(is_mandatory=True)
    elective_units = available_units.filter(is_mandatory=False)
    
    context = {
        'current_semester': current_semester,
        'mandatory_units': mandatory_units,
        'elective_units': elective_units,
        'enrolled_unit_ids': enrolled_unit_ids,
        'registration_deadline': registration_deadline,
    }
    
    return render(request, 'student/units/register_units.html', context)


@login_required(login_url='login')
def student_enrollments(request):
    """View student enrollments organized by academic year and semester"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    # Get all enrollments grouped by academic year
    enrollments = UnitEnrollment.objects.filter(
        student=student
    ).select_related('unit', 'semester', 'semester__academic_year').order_by(
        '-semester__academic_year__start_date',
        '-semester__semester_number'
    )
    
    # Organize by academic year
    enrollments_by_year = {}
    for enrollment in enrollments:
        year_code = enrollment.semester.academic_year.year_code
        if year_code not in enrollments_by_year:
            enrollments_by_year[year_code] = {
                'academic_year': enrollment.semester.academic_year,
                'semesters': {}
            }
        
        sem_num = enrollment.semester.semester_number
        if sem_num not in enrollments_by_year[year_code]['semesters']:
            enrollments_by_year[year_code]['semesters'][sem_num] = {
                'semester': enrollment.semester,
                'units': []
            }
        
        enrollments_by_year[year_code]['semesters'][sem_num]['units'].append(enrollment)
    
    # Calculate registration dates for drop eligibility
    current_date = timezone.now().date()
    for year_code in enrollments_by_year:
        for sem_num in enrollments_by_year[year_code]['semesters']:
            for enrollment in enrollments_by_year[year_code]['semesters'][sem_num]['units']:
                registration_date = enrollment.enrollment_date.date()
                drop_eligible_date = registration_date + timedelta(days=7)
                enrollment.can_drop = current_date >= drop_eligible_date
                enrollment.days_until_drop = (drop_eligible_date - current_date).days
    
    context = {
        'enrollments_by_year': enrollments_by_year,
        'total_enrollments': enrollments.count(),
    }
    
    return render(request, 'student/units/student_enrollments.html', context)


@login_required(login_url='login')
def drop_unit(request, enrollment_id):
    """Drop a unit (after 7 days from registration)"""
    if request.method != 'POST':
        return redirect('student_enrollments')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    enrollment = get_object_or_404(
        UnitEnrollment,
        id=enrollment_id,
        student=student
    )
    
    # Check if within 7 days
    registration_date = enrollment.enrollment_date.date()
    current_date = timezone.now().date()
    drop_eligible_date = registration_date + timedelta(days=7)
    
    if current_date < drop_eligible_date:
        days_remaining = (drop_eligible_date - current_date).days
        messages.error(
            request,
            f"You can only drop this unit after {days_remaining} more day(s) "
            f"(eligible from {drop_eligible_date})."
        )
        return redirect('student_enrollments')
    
    unit_name = enrollment.unit.name
    unit_code = enrollment.unit.code
    
    # Mark as dropped
    enrollment.status = 'DROPPED'
    enrollment.save()
    
    # Update semester registration count
    sem_registration = SemesterRegistration.objects.filter(
        student=student,
        semester=enrollment.semester
    ).first()
    
    if sem_registration:
        sem_registration.units_enrolled = UnitEnrollment.objects.filter(
            student=student,
            semester=enrollment.semester,
            status__in=['ENROLLED', 'COMPLETED']
        ).count()
        sem_registration.save()
    
    messages.success(request, f"Successfully dropped {unit_code} - {unit_name}.")
    return redirect('student_enrollments')


# views.py - Student Programme Curriculum View
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Student, ProgrammeUnit, Unit


@login_required(login_url='login')
def my_programme(request):
    """View the complete curriculum of student's programme"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    programme = student.programme
    
    # Get all programme units organized by year and semester
    programme_units = ProgrammeUnit.objects.filter(
        programme=programme
    ).select_related('unit').order_by('year_level', 'semester')
    
    # Organize by year and semester
    curriculum_by_year = {}
    for program_unit in programme_units:
        year_level = program_unit.year_level
        semester = program_unit.semester
        
        if year_level not in curriculum_by_year:
            curriculum_by_year[year_level] = {
                'year_label': f'Year {year_level}',
                'semesters': {}
            }
        
        if semester not in curriculum_by_year[year_level]['semesters']:
            curriculum_by_year[year_level]['semesters'][semester] = {
                'semester_label': f'Semester {semester}',
                'mandatory_units': [],
                'elective_units': [],
                'total_credits': 0
            }
        
        semester_data = curriculum_by_year[year_level]['semesters'][semester]
        
        if program_unit.is_mandatory:
            semester_data['mandatory_units'].append(program_unit)
        else:
            semester_data['elective_units'].append(program_unit)
        
        semester_data['total_credits'] += program_unit.unit.credit_hours
    
    # Calculate programme statistics
    total_units = programme_units.count()
    total_credits = sum(pu.unit.credit_hours for pu in programme_units)
    mandatory_units = programme_units.filter(is_mandatory=True).count()
    elective_units = programme_units.filter(is_mandatory=False).count()
    
    context = {
        'programme': programme,
        'curriculum_by_year': curriculum_by_year,
        'total_units': total_units,
        'total_credits': total_credits,
        'mandatory_units': mandatory_units,
        'elective_units': elective_units,
        'programme_duration': programme.duration_years,
        'semesters_per_year': programme.semesters_per_year,
    }
    
    return render(request, 'student/programme/view_curriculum.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from .models import Student, User
from .forms import StudentProfileForm, UserProfileForm

@login_required
def student_profile_view(request):
    """
    Combined view for viewing and editing student profile
    """
    # Ensure user is a student
    if request.user.user_type != 'STUDENT':
        messages.error(request, "Access denied. This page is only for students.")
        return redirect('student_dashboard')
    
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    # Handle form submission
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            user_form = UserProfileForm(request.POST, request.FILES, instance=request.user)
            student_form = StudentProfileForm(request.POST, instance=student)
            
            if user_form.is_valid() and student_form.is_valid():
                try:
                    with transaction.atomic():
                        user_form.save()
                        student_form.save()
                    messages.success(request, "Profile updated successfully!")
                    return redirect('student_profile')
                except Exception as e:
                    messages.error(request, f"Error updating profile: {str(e)}")
            else:
                messages.error(request, "Please correct the errors below.")
        
        elif action == 'change_password':
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, "Your password was successfully updated!")
                return redirect('student_profile')
            else:
                messages.error(request, "Please correct the password errors below.")
                # Pass the form with errors to the context
                context = {
                    'student': student,
                    'user_form': UserProfileForm(instance=request.user),
                    'student_form': StudentProfileForm(instance=student),
                    'password_form': password_form,
                    'show_password_modal': True
                }
                return render(request, 'student/profile.html', context)
    
    
    # GET request - display forms
    user_form = UserProfileForm(instance=request.user)
    student_form = StudentProfileForm(instance=student)
    password_form = PasswordChangeForm(request.user)
    
    context = {
        'student': student,
        'user_form': user_form,
        'student_form': student_form,
        'password_form': password_form,
        'show_password_modal': False
    }
    
    return render(request, 'student/profile.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Student, Semester, SemesterRegistration, AcademicYear

@login_required
def student_semester_reporting(request):
    """
    View for students to report for the current semester
    """
    # Ensure user is a student
    if request.user.user_type != 'STUDENT':
        messages.error(request, "Access denied. This page is only for students.")
        return redirect('student_dashboard')
    
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    # Get current semester
    try:
        current_semester = Semester.objects.get(is_current=True)
        current_academic_year = current_semester.academic_year
    except Semester.DoesNotExist:
        current_semester = None
        current_academic_year = None
    
    # Check if student's programme allows reporting
    can_report = False
    is_on_holiday = False
    holiday_message = None
    
    if current_semester and student.programme.semesters_per_year == 2:
        # Programme has 2 semesters per year
        if current_semester.semester_number in [1, 2]:
            can_report = True
        elif current_semester.semester_number == 3:
            is_on_holiday = True
            holiday_message = f"Your programme ({student.programme.name}) has 2 semesters per academic year. Semester 3 is a holiday period for your programme."
    elif current_semester and student.programme.semesters_per_year == 3:
        # Programme has 3 semesters per year - can always report
        can_report = True
    
    # Check if already registered for current semester
    already_registered = False
    registration = None
    if current_semester:
        registration = SemesterRegistration.objects.filter(
            student=student,
            semester=current_semester
        ).first()
        
        if registration:
            already_registered = True
    
    # Check registration deadline
    registration_open = False
    deadline_passed = False
    if current_semester and can_report:
        today = timezone.now().date()
        if today <= current_semester.registration_deadline:
            registration_open = True
        else:
            deadline_passed = True
    
    # Handle form submission
    if request.method == 'POST' and can_report and registration_open and not already_registered:
        action = request.POST.get('action')
        
        if action == 'report_semester':
            try:
                with transaction.atomic():
                    # Create semester registration
                    registration = SemesterRegistration.objects.create(
                        student=student,
                        semester=current_semester,
                        status='REGISTERED',
                        units_enrolled=0  # Will be updated during unit enrollment
                    )
                    
                    messages.success(
                        request, 
                        f"Successfully reported for {current_semester}! You can now proceed to enroll in units."
                    )
                    return redirect('student_semester_reporting')
                    
            except Exception as e:
                messages.error(request, f"Error reporting for semester: {str(e)}")
    
    # Get previous registrations
    previous_registrations = SemesterRegistration.objects.filter(
        student=student
    ).select_related('semester', 'semester__academic_year').order_by('-registration_date')[:5]
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'current_academic_year': current_academic_year,
        'can_report': can_report,
        'is_on_holiday': is_on_holiday,
        'holiday_message': holiday_message,
        'already_registered': already_registered,
        'registration': registration,
        'registration_open': registration_open,
        'deadline_passed': deadline_passed,
        'previous_registrations': previous_registrations,
    }
    
    return render(request, 'student/semester_reporting.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from .models import (
    Student, Event, Announcement, Semester, 
    AcademicYear, TimetableSlot
)

@login_required
def student_academic_calendar(request):
    """
    Academic calendar view showing events, announcements, and important dates
    """
    # Ensure user is a student
    if request.user.user_type != 'STUDENT':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student profile not found'}, status=404)
    
    # Get current date or requested month/year
    today = timezone.now().date()
    
    # Get month and year from query params or use current
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        month = today.month
        year = today.year
    
    # Validate month and year
    if month < 1 or month > 12:
        month = today.month
    if year < 2000 or year > 2100:
        year = today.year
    
    # Get calendar data
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Get date range for the month
    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Get events for this month targeting student's programme
    events = Event.objects.filter(
        event_date__gte=first_day,
        event_date__lte=last_day,
        is_published=True
    ).filter(
        target_programmes=student.programme
    ).select_related('venue', 'organizer')
    
    # Get announcements published in this month
    announcements = Announcement.objects.filter(
        publish_date__date__gte=first_day,
        publish_date__date__lte=last_day,
        is_published=True
    ).filter(
        target_programmes=student.programme
    ).select_related('created_by')
    
    # Get semesters
    semesters = Semester.objects.filter(
        start_date__lte=last_day,
        end_date__gte=first_day
    ).select_related('academic_year')
    
    # Get timetable slots for the month
    timetable_slots = TimetableSlot.objects.filter(
        programme=student.programme,
        year_level=student.current_year,
        is_active=True,
        unit_allocation__semester__start_date__lte=last_day,
        unit_allocation__semester__end_date__gte=first_day
    ).select_related(
        'unit_allocation__unit',
        'unit_allocation__lecturer__user',
        'venue'
    )
    
    # Organize data by date
    calendar_data = {}
    
    # Add events
    for event in events:
        date_key = event.event_date.strftime('%Y-%m-%d')
        if date_key not in calendar_data:
            calendar_data[date_key] = {
                'events': [],
                'announcements': [],
                'semesters': [],
                'classes': []
            }
        calendar_data[date_key]['events'].append({
            'id': event.id,
            'title': event.title,
            'type': event.event_type,
            'time': event.start_time.strftime('%H:%M'),
            'venue': event.venue.name if event.venue else 'TBA',
            'is_mandatory': event.is_mandatory,
            'icon': get_event_icon(event.event_type)
        })
    
    # Add announcements
    for announcement in announcements:
        date_key = announcement.publish_date.date().strftime('%Y-%m-%d')
        if date_key not in calendar_data:
            calendar_data[date_key] = {
                'events': [],
                'announcements': [],
                'semesters': [],
                'classes': []
            }
        calendar_data[date_key]['announcements'].append({
            'id': announcement.id,
            'title': announcement.title,
            'priority': announcement.priority,
            'author': announcement.created_by.get_full_name()
        })
    
    # Add semester start/end dates
    for semester in semesters:
        # Start date
        if first_day <= semester.start_date <= last_day:
            date_key = semester.start_date.strftime('%Y-%m-%d')
            if date_key not in calendar_data:
                calendar_data[date_key] = {
                    'events': [],
                    'announcements': [],
                    'semesters': [],
                    'classes': []
                }
            calendar_data[date_key]['semesters'].append({
                'title': f'{semester} - Starts',
                'type': 'start',
                'semester': str(semester)
            })
        
        # End date
        if first_day <= semester.end_date <= last_day:
            date_key = semester.end_date.strftime('%Y-%m-%d')
            if date_key not in calendar_data:
                calendar_data[date_key] = {
                    'events': [],
                    'announcements': [],
                    'semesters': [],
                    'classes': []
                }
            calendar_data[date_key]['semesters'].append({
                'title': f'{semester} - Ends',
                'type': 'end',
                'semester': str(semester)
            })
        
        # Registration deadline
        if first_day <= semester.registration_deadline <= last_day:
            date_key = semester.registration_deadline.strftime('%Y-%m-%d')
            if date_key not in calendar_data:
                calendar_data[date_key] = {
                    'events': [],
                    'announcements': [],
                    'semesters': [],
                    'classes': []
                }
            calendar_data[date_key]['semesters'].append({
                'title': f'{semester} - Registration Deadline',
                'type': 'deadline',
                'semester': str(semester)
            })
    
    # Add class schedule summary (count of classes per day)
    for slot in timetable_slots:
        # Get all dates in the month that match this day of week
        for week in cal:
            for day in week:
                if day == 0:  # Skip empty days
                    continue
                date_obj = datetime(year, month, day).date()
                day_name = date_obj.strftime('%A').upper()
                
                if day_name == slot.day_of_week:
                    date_key = date_obj.strftime('%Y-%m-%d')
                    if date_key not in calendar_data:
                        calendar_data[date_key] = {
                            'events': [],
                            'announcements': [],
                            'semesters': [],
                            'classes': []
                        }
                    calendar_data[date_key]['classes'].append({
                        'unit': slot.unit_allocation.unit.code,
                        'time': slot.start_time.strftime('%H:%M'),
                        'venue': slot.venue.code
                    })
    
    # Calculate previous and next month
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    context = {
        'student': student,
        'calendar': cal,
        'month': month,
        'year': year,
        'month_name': month_name,
        'today': today,
        'calendar_data': calendar_data,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }
    
    return render(request, 'student/academic_calendar.html', context)


def get_event_icon(event_type):
    """Return Bootstrap icon class for event type"""
    icons = {
        'SEMINAR': 'bi-people',
        'WORKSHOP': 'bi-tools',
        'CONFERENCE': 'bi-briefcase',
        'MEETING': 'bi-person-video3',
        'ORIENTATION': 'bi-compass',
        'EXAMINATION': 'bi-clipboard-check',
        'OTHER': 'bi-calendar-event',
    }
    return icons.get(event_type, 'bi-calendar-event')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import datetime, time
from collections import defaultdict
from .models import Student, TimetableSlot, Semester

@login_required
def student_timetable_view(request):
    """
    View for students to see their personalized timetable
    """
    # Ensure user is a student
    if request.user.user_type != 'STUDENT':
        messages.error(request, "Access denied. This page is only for students.")
        return redirect('student_dashboard')
    
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')
    
    # Get current semester
    try:
        current_semester = Semester.objects.get(is_current=True)
    except Semester.DoesNotExist:
        current_semester = None
    
    # Get timetable slots for the student's programme and year level
    timetable_slots = []
    if current_semester:
        timetable_slots = TimetableSlot.objects.filter(
            programme=student.programme,
            year_level=student.current_year,
            unit_allocation__semester=current_semester,
            is_active=True
        ).select_related(
            'unit_allocation__unit',
            'unit_allocation__lecturer__user',
            'venue'
        ).order_by('day_of_week', 'start_time')
    
    # Define days of the week in order
    days_order = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    
    # Organize slots by day and time
    timetable_by_day = defaultdict(list)
    all_time_slots = set()
    
    for slot in timetable_slots:
        timetable_by_day[slot.day_of_week].append(slot)
        # Create time slot key (e.g., "08:00-10:00")
        time_key = f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
        all_time_slots.add((slot.start_time, slot.end_time, time_key))
    
    # Sort time slots
    sorted_time_slots = sorted(list(all_time_slots), key=lambda x: x[0])
    
    # Create a structured timetable grid
    timetable_grid = {}
    for day in days_order:
        timetable_grid[day] = {}
        for start_time, end_time, time_key in sorted_time_slots:
            timetable_grid[day][time_key] = None
    
    # Fill in the timetable grid
    for slot in timetable_slots:
        time_key = f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
        if slot.day_of_week in timetable_grid and time_key in timetable_grid[slot.day_of_week]:
            timetable_grid[slot.day_of_week][time_key] = {
                'unit_code': slot.unit_allocation.unit.code,
                'unit_name': slot.unit_allocation.unit.name,
                'lecturer': slot.unit_allocation.lecturer.user.get_full_name(),
                'venue': slot.venue.code,
                'venue_name': slot.venue.name,
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
            }
    
    # Calculate statistics
    total_classes = len(timetable_slots)
    unique_units = len(set([slot.unit_allocation.unit for slot in timetable_slots]))
    
    # Count classes per day
    classes_per_day = {}
    for day in days_order:
        classes_per_day[day] = len(timetable_by_day.get(day, []))
    
    context = {
        'student': student,
        'current_semester': current_semester,
        'timetable_slots': timetable_slots,
        'timetable_grid': timetable_grid,
        'days_order': days_order,
        'sorted_time_slots': sorted_time_slots,
        'total_classes': total_classes,
        'unique_units': unique_units,
        'classes_per_day': classes_per_day,
    }
    
    return render(request, 'student/timetable.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
import traceback

from .models import User, Message, MessageReadStatus

# ========================
# MESSAGING VIEWS
# ========================

@login_required
def messaging_list(request):
    """
    Main messaging page - shows conversation list and chat area
    """
    user = request.user
    
    try:
        # Get all messages involving this user
        all_messages = Message.objects.filter(
            Q(sender=user) | Q(recipients=user)
        ).select_related('sender').prefetch_related('recipients').order_by('-sent_at')
        
        # Get unique conversation partners manually (SQLite compatible)
        conversation_partners = {}
        for msg in all_messages:
            if msg.sender == user:
                partner = msg.recipients.first()
            else:
                partner = msg.sender
            
            if partner and partner.id not in conversation_partners:
                conversation_partners[partner.id] = {
                    'user': partner,
                    'last_message': msg,
                }
        
        # Build conversation list with unread counts
        conversation_list = []
        for partner_id, conv_data in conversation_partners.items():
            partner = conv_data['user']
            last_msg = conv_data['last_message']
            
            unread_count = MessageReadStatus.objects.filter(
                message__sender=partner,
                recipient=user,
                is_read=False
            ).count()
            
            conversation_list.append({
                'user': partner,
                'last_message': last_msg,
                'unread_count': unread_count,
            })
        
        conversation_list.sort(key=lambda x: x['last_message'].sent_at, reverse=True)
        
        context = {
            'conversations': conversation_list,
            'user_type': user.user_type,
        }
        return render(request, 'messaging/message_list.html', context)
    
    except Exception as e:
        print(f"Error in messaging_list: {str(e)}")
        traceback.print_exc()
        return render(request, 'messaging/message_list.html', {'conversations': [], 'error': str(e)})


@login_required
def message_thread(request, user_id):
    """
    Get message thread between current user and specified user
    """
    current_user = request.user
    
    try:
        other_user = get_object_or_404(User, id=user_id)
        
        if current_user == other_user:
            return JsonResponse({'error': 'Cannot message yourself'}, status=400)
        
        # Get all messages between these two users
        messages = Message.objects.filter(
            Q(sender=current_user, recipients=other_user) |
            Q(sender=other_user, recipients=current_user)
        ).select_related('sender').order_by('sent_at')
        
        # Mark messages as read
        MessageReadStatus.objects.filter(
            message__sender=other_user,
            recipient=current_user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        # Prepare message data - ensure all values are strings/primitives
        message_data = []
        for msg in messages:
            read_status = MessageReadStatus.objects.filter(
                message=msg,
                recipient=current_user
            ).first()
            
            # Convert datetime to ISO string
            sent_at = msg.sent_at.isoformat() if hasattr(msg.sent_at, 'isoformat') else str(msg.sent_at)
            
            message_data.append({
                'id': int(msg.id),
                'sender': str(msg.sender.get_full_name() or msg.sender.username),
                'sender_id': int(msg.sender.id),
                'body': str(msg.body),
                'sent_at': sent_at,
                'is_own': bool(msg.sender == current_user),
                'is_read': bool(read_status.is_read if read_status else False),
            })
        
        # Build profile info - ensure all strings
        registration_number = ''
        programme = ''
        staff_number = ''
        department = ''
        
        try:
            if other_user.user_type == 'STUDENT' and hasattr(other_user, 'student_profile'):
                registration_number = str(other_user.student_profile.registration_number)
                programme = str(other_user.student_profile.programme)
        except Exception as e:
            print(f"Error getting student profile: {str(e)}")
        
        try:
            if other_user.user_type == 'LECTURER' and hasattr(other_user, 'lecturer_profile'):
                staff_number = str(other_user.lecturer_profile.staff_number)
                department = str(other_user.lecturer_profile.department)
        except Exception as e:
            print(f"Error getting lecturer profile: {str(e)}")
        
        profile_info = {
            'id': int(other_user.id),
            'name': str(other_user.get_full_name() or other_user.username),
            'email': str(other_user.email or ''),
            'phone': str(other_user.phone_number or ''),
            'user_type': str(other_user.get_user_type_display() or 'User'),
            'registration_number': registration_number,
            'programme': programme,
            'staff_number': staff_number,
            'department': department,
        }
        
        return JsonResponse({
            'success': True,
            'other_user': {
                'id': int(other_user.id),
                'name': str(other_user.get_full_name() or other_user.username),
            },
            'profile_info': profile_info,
            'messages': message_data,
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        print(f"Error in message_thread: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_message(request, user_id):
    """
    Send a message to a user (AJAX)
    """
    current_user = request.user
    
    try:
        recipient = get_object_or_404(User, id=user_id)
        
        if current_user == recipient:
            return JsonResponse({'error': 'Cannot message yourself'}, status=400)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        body = data.get('message', '').strip()
        
        if not body:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        if len(body) > 5000:
            return JsonResponse({'error': 'Message is too long'}, status=400)
        
        # Create message
        message = Message.objects.create(
            sender=current_user,
            subject='Direct Message',
            body=body,
            message_type='DIRECT'
        )
        message.recipients.add(recipient)
        
        # Create read status
        MessageReadStatus.objects.create(
            message=message,
            recipient=recipient,
            is_read=False
        )
        
        sent_at = message.sent_at.isoformat() if hasattr(message.sent_at, 'isoformat') else str(message.sent_at)
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': int(message.id),
                'sender': str(current_user.get_full_name() or current_user.username),
                'sender_id': int(current_user.id),
                'body': str(message.body),
                'sent_at': sent_at,
                'is_own': True,
                'is_read': False,
            }
        })
    
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def search_users(request):
    """
    Search for users to message (AJAX)
    """
    query = request.GET.get('q', '').strip()
    current_user = request.user
    
    try:
        if not query or len(query) < 2:
            return JsonResponse({'users': []})
        
        # Search by name and email
        users = User.objects.filter(
            ~Q(id=current_user.id),
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).select_related('student_profile', 'lecturer_profile').distinct()[:10]
        
        # Also search by registration/staff number
        try:
            student_users = User.objects.filter(
                ~Q(id=current_user.id),
                student_profile__registration_number__icontains=query
            ).select_related('student_profile')[:5]
            
            lecturer_users = User.objects.filter(
                ~Q(id=current_user.id),
                lecturer_profile__staff_number__icontains=query
            ).select_related('lecturer_profile')[:5]
            
            user_ids = set()
            combined_users = []
            
            for u in users:
                if u.id not in user_ids:
                    combined_users.append(u)
                    user_ids.add(u.id)
            
            for u in student_users:
                if u.id not in user_ids:
                    combined_users.append(u)
                    user_ids.add(u.id)
                    
            for u in lecturer_users:
                if u.id not in user_ids:
                    combined_users.append(u)
                    user_ids.add(u.id)
            
            users = combined_users[:10]
        except Exception as e:
            print(f"Error searching by ID: {str(e)}")
        
        users_data = []
        for user in users:
            identifier = ''
            
            try:
                if user.user_type == 'STUDENT' and hasattr(user, 'student_profile'):
                    identifier = str(user.student_profile.registration_number)
                elif user.user_type == 'LECTURER' and hasattr(user, 'lecturer_profile'):
                    identifier = str(user.lecturer_profile.staff_number)
            except Exception as e:
                print(f"Error getting identifier: {str(e)}")
            
            user_info = {
                'id': int(user.id),
                'name': str(user.get_full_name() or user.username),
                'email': str(user.email or ''),
                'user_type': str(user.get_user_type_display() or 'User'),
                'type_code': str(user.user_type or ''),
                'identifier': identifier,
            }
            
            users_data.append(user_info)
        
        return JsonResponse({'users': users_data})
    
    except Exception as e:
        print(f"Error in search_users: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def mark_as_read(request, message_id):
    """
    Mark a message as read (AJAX)
    """
    try:
        message = get_object_or_404(Message, id=message_id)
        
        read_status = MessageReadStatus.objects.filter(
            message=message,
            recipient=request.user
        ).first()
        
        if read_status:
            read_status.is_read = True
            read_status.read_at = timezone.now()
            read_status.save()
            return JsonResponse({'success': True})
        
        return JsonResponse({'error': 'Read status not found'}, status=404)
    except Exception as e:
        print(f"Error in mark_as_read: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """
    Get total unread message count (AJAX)
    """
    try:
        unread_count = MessageReadStatus.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return JsonResponse({'unread_count': int(unread_count)})
    except Exception as e:
        print(f"Error in get_unread_count: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_conversation(request, user_id):
    """
    Delete a conversation (AJAX)
    """
    try:
        current_user = request.user
        other_user = get_object_or_404(User, id=user_id)
        
        # Delete messages between these users
        Message.objects.filter(
            Q(sender=current_user, recipients=other_user) |
            Q(sender=other_user, recipients=current_user)
        ).delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error in delete_conversation: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)




from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count, Q, F
from decimal import Decimal
from collections import defaultdict

@login_required
def student_grades_view(request):
    """View for displaying student grades organized by year and semester"""
    
    # Get student profile
    try:
        student = request.user.student_profile
    except:
        return render(request, 'error.html', {'message': 'Student profile not found'})
    
    # Get all enrollments with final grades
    enrollments = UnitEnrollment.objects.filter(
        student=student,
        status='COMPLETED'
    ).select_related(
        'unit',
        'semester',
        'semester__academic_year',
        'final_grade'
    ).prefetch_related(
        'marks__assessment_component'
    ).order_by(
        'semester__academic_year__start_date',
        'semester__semester_number'
    )
    
    # Organize grades by year and semester
    grades_by_year = defaultdict(lambda: {
        'year_label': '',
        'semesters': defaultdict(lambda: {
            'semester_label': '',
            'academic_year': '',
            'units': [],
            'total_units': 0,
            'total_credits': 0,
            'semester_gpa': Decimal('0.00'),
            'graded_units': 0
        })
    })
    
    total_credits_earned = 0
    total_grade_points = Decimal('0.00')
    total_units_completed = 0
    
    for enrollment in enrollments:
        semester = enrollment.semester
        academic_year = semester.academic_year
        
        # Determine year level from program unit
        try:
            program_unit = ProgrammeUnit.objects.get(
                programme=student.programme,
                unit=enrollment.unit
            )
            year_level = program_unit.year_level
        except:
            # Fallback to student's enrollment year
            year_level = student.current_year
        
        semester_num = semester.semester_number
        
        # Get assessment breakdown
        assessment_breakdown = []
        total_marks = Decimal('0.00')
        
        marks = enrollment.marks.all().select_related('assessment_component')
        for mark in marks:
            component = mark.assessment_component
            # Calculate weighted marks
            weighted_marks = (mark.marks_obtained / component.max_marks) * component.weight_percentage
            total_marks += weighted_marks
            
            assessment_breakdown.append({
                'name': component.name,
                'type': component.get_component_type_display(),
                'weight': component.weight_percentage,
                'max_marks': component.max_marks,
                'marks_obtained': mark.marks_obtained,
                'weighted_marks': weighted_marks,
                'percentage': (mark.marks_obtained / component.max_marks) * 100 if component.max_marks > 0 else 0
            })
        
        # Get final grade
        unit_data = {
            'unit_code': enrollment.unit.code,
            'unit_name': enrollment.unit.name,
            'credit_hours': enrollment.unit.credit_hours,
            'assessment_breakdown': assessment_breakdown,
            'total_marks': total_marks,
            'grade': None,
            'grade_point': None,
            'has_grade': False
        }
        
        if hasattr(enrollment, 'final_grade'):
            final_grade = enrollment.final_grade
            unit_data.update({
                'grade': final_grade.grade,
                'grade_point': final_grade.grade_point,
                'total_marks': final_grade.total_marks,
                'has_grade': True
            })
            
            # Calculate totals for GPA
            if final_grade.grade_point > 0:
                total_credits_earned += enrollment.unit.credit_hours
                total_grade_points += (final_grade.grade_point * enrollment.unit.credit_hours)
                total_units_completed += 1
        
        # Add to structure
        year_data = grades_by_year[year_level]
        year_data['year_label'] = f'Year {year_level}'
        
        semester_data = year_data['semesters'][semester_num]
        semester_data['semester_label'] = f'Semester {semester_num}'
        semester_data['academic_year'] = academic_year.year_code
        semester_data['units'].append(unit_data)
        semester_data['total_units'] += 1
        semester_data['total_credits'] += enrollment.unit.credit_hours
        
        if unit_data['has_grade']:
            semester_data['graded_units'] += 1
    
    # Calculate semester GPAs
    for year_level, year_data in grades_by_year.items():
        for semester_num, semester_data in year_data['semesters'].items():
            semester_credits = Decimal('0.00')
            semester_points = Decimal('0.00')
            
            for unit in semester_data['units']:
                if unit['has_grade'] and unit['grade_point']:
                    semester_credits += unit['credit_hours']
                    semester_points += (unit['grade_point'] * unit['credit_hours'])
            
            if semester_credits > 0:
                semester_data['semester_gpa'] = round(semester_points / semester_credits, 2)
    
    # Calculate cumulative GPA
    cumulative_gpa = Decimal('0.00')
    if total_credits_earned > 0:
        cumulative_gpa = round(total_grade_points / total_credits_earned, 2)
    
    # Sort the data
    grades_by_year = dict(sorted(grades_by_year.items()))
    for year_level in grades_by_year:
        grades_by_year[year_level]['semesters'] = dict(
            sorted(grades_by_year[year_level]['semesters'].items())
        )
    
    context = {
        'student': student,
        'programme': student.programme,
        'grades_by_year': grades_by_year,
        'cumulative_gpa': cumulative_gpa,
        'total_credits_earned': total_credits_earned,
        'total_units_completed': total_units_completed,
        'current_year': student.current_year,
    }
    
    return render(request, 'student/my_grades.html', context)


@login_required
def academic_performance_view(request):
    """View for displaying overall academic performance with classification"""
    
    # Get student profile
    try:
        student = request.user.student_profile
    except:
        return render(request, 'error.html', {'message': 'Student profile not found'})
    
    # Get all completed enrollments with grades
    enrollments = UnitEnrollment.objects.filter(
        student=student,
        status='COMPLETED',
        final_grade__isnull=False
    ).select_related(
        'unit',
        'semester',
        'semester__academic_year',
        'final_grade'
    ).order_by(
        'semester__academic_year__start_date',
        'semester__semester_number'
    )
    
    # Calculate overall statistics
    total_credits_earned = 0
    total_grade_points = Decimal('0.00')
    total_units = 0
    grade_distribution = defaultdict(int)
    
    # Performance by year
    performance_by_year = defaultdict(lambda: {
        'year_label': '',
        'semesters': [],
        'total_credits': 0,
        'total_grade_points': Decimal('0.00'),
        'year_gpa': Decimal('0.00'),
        'units_count': 0
    })
    
    # Performance by semester
    semester_performance = []
    
    current_semester_data = {}
    
    for enrollment in enrollments:
        final_grade = enrollment.final_grade
        semester = enrollment.semester
        
        # Get year level
        try:
            program_unit = ProgrammeUnit.objects.get(
                programme=student.programme,
                unit=enrollment.unit
            )
            year_level = program_unit.year_level
        except:
            year_level = student.current_year
        
        credits = enrollment.unit.credit_hours
        grade_point = final_grade.grade_point
        
        # Overall totals
        total_credits_earned += credits
        total_grade_points += (grade_point * credits)
        total_units += 1
        grade_distribution[final_grade.grade] += 1
        
        # Year performance
        year_data = performance_by_year[year_level]
        year_data['year_label'] = f'Year {year_level}'
        year_data['total_credits'] += credits
        year_data['total_grade_points'] += (grade_point * credits)
        year_data['units_count'] += 1
        
        # Semester data
        semester_key = f"{semester.academic_year.year_code}-{semester.semester_number}"
        if semester_key not in current_semester_data:
            current_semester_data[semester_key] = {
                'semester': semester,
                'academic_year': semester.academic_year.year_code,
                'semester_number': semester.semester_number,
                'semester_label': f'Semester {semester.semester_number}',
                'year_level': year_level,
                'credits': 0,
                'grade_points': Decimal('0.00'),
                'gpa': Decimal('0.00'),
                'units_count': 0,
                'grades': []
            }
        
        sem_data = current_semester_data[semester_key]
        sem_data['credits'] += credits
        sem_data['grade_points'] += (grade_point * credits)
        sem_data['units_count'] += 1
        sem_data['grades'].append({
            'unit_code': enrollment.unit.code,
            'unit_name': enrollment.unit.name,
            'grade': final_grade.grade,
            'grade_point': grade_point,
            'credits': credits
        })
    
    # Calculate GPAs
    cumulative_gpa = Decimal('0.00')
    if total_credits_earned > 0:
        cumulative_gpa = round(total_grade_points / total_credits_earned, 2)
    
    # Calculate year GPAs
    for year_level, year_data in performance_by_year.items():
        if year_data['total_credits'] > 0:
            year_data['year_gpa'] = round(
                year_data['total_grade_points'] / year_data['total_credits'],
                2
            )
    
    # Calculate semester GPAs
    for sem_data in current_semester_data.values():
        if sem_data['credits'] > 0:
            sem_data['gpa'] = round(sem_data['grade_points'] / sem_data['credits'], 2)
        semester_performance.append(sem_data)
    
    # Sort semester performance by date
    semester_performance.sort(
        key=lambda x: (x['semester'].academic_year.start_date, x['semester_number'])
    )
    
    # Group semesters by year for display
    for sem_data in semester_performance:
        year_level = sem_data['year_level']
        performance_by_year[year_level]['semesters'].append(sem_data)
    
    # Determine degree classification
    classification = get_degree_classification(cumulative_gpa, student.programme.level)
    
    # Calculate progression metrics
    credits_required = student.programme.duration_years * 30  # Assuming 30 credits per year
    progress_percentage = (total_credits_earned / credits_required * 100) if credits_required > 0 else 0
    
    # Grade distribution for chart
    grade_dist_list = [
        {'grade': grade, 'count': count}
        for grade, count in sorted(grade_distribution.items())
    ]
    
    # Sort performance by year
    performance_by_year = dict(sorted(performance_by_year.items()))
    
    context = {
        'student': student,
        'programme': student.programme,
        'cumulative_gpa': cumulative_gpa,
        'classification': classification,
        'total_credits_earned': total_credits_earned,
        'total_units': total_units,
        'credits_required': credits_required,
        'progress_percentage': round(progress_percentage, 1),
        'performance_by_year': performance_by_year,
        'semester_performance': semester_performance,
        'grade_distribution': grade_dist_list,
        'highest_gpa_semester': max(semester_performance, key=lambda x: x['gpa']) if semester_performance else None,
        'lowest_gpa_semester': min(semester_performance, key=lambda x: x['gpa']) if semester_performance else None,
    }
    
    return render(request, 'student/academic_performance.html', context)


def get_degree_classification(gpa, programme_level):
    """Determine degree classification based on GPA and programme level"""
    
    # Only classify for Bachelor's degree
    if programme_level != 'BACHELORS':
        if gpa >= 3.5:
            return {
                'class': 'Distinction',
                'color': '#16A34A',
                'description': 'Outstanding Performance'
            }
        elif gpa >= 3.0:
            return {
                'class': 'Credit',
                'color': '#2563EB',
                'description': 'Very Good Performance'
            }
        elif gpa >= 2.0:
            return {
                'class': 'Pass',
                'color': '#F59E0B',
                'description': 'Good Performance'
            }
        else:
            return {
                'class': 'Below Pass',
                'color': '#DC2626',
                'description': 'Needs Improvement'
            }
    
    # Bachelor's degree classification
    if gpa >= 3.60:
        return {
            'class': 'First Class Honours',
            'color': '#16A34A',
            'description': 'Exceptional Academic Achievement'
        }
    elif gpa >= 3.00:
        return {
            'class': 'Second Class Honours (Upper Division)',
            'color': '#2563EB',
            'description': 'Very Good Academic Performance'
        }
    elif gpa >= 2.50:
        return {
            'class': 'Second Class Honours (Lower Division)',
            'color': '#7C3AED',
            'description': 'Good Academic Performance'
        }
    elif gpa >= 2.00:
        return {
            'class': 'Pass',
            'color': '#F59E0B',
            'description': 'Satisfactory Performance'
        }
    else:
        return {
            'class': 'Fail',
            'color': '#DC2626',
            'description': 'Below Minimum Requirement'
        }
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from .models import (
    Student, UnitEnrollment, Semester, AcademicYear, 
    Unit, AssessmentComponent, StudentMarks, FinalGrade,
    Lecturer, GradingScheme
)


def is_admin_or_staff(user):
    """Check if user is admin or staff"""
    return user.is_staff or user.is_superuser or user.user_type in ['COD', 'DEAN', 'ICT_ADMIN']


@login_required
@user_passes_test(is_admin_or_staff)
def marks_entry_view(request):
    """Main view for marks entry - search student and select semester"""
    
    # Get all active academic years and semesters
    academic_years = AcademicYear.objects.filter(is_current=True).order_by('-start_date')
    semesters = Semester.objects.filter(
        academic_year__is_current=True
    ).select_related('academic_year').order_by('-academic_year__start_date', '-semester_number')
    
    # Also get past semesters for reference
    past_semesters = Semester.objects.filter(
        is_current=False
    ).select_related('academic_year').order_by('-academic_year__start_date', '-semester_number')[:10]
    
    all_semesters = list(semesters) + list(past_semesters)
    
    context = {
        'academic_years': academic_years,
        'semesters': all_semesters,
    }
    
    return render(request, 'admin/marks_entry.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def search_student_ajax(request):
    """AJAX endpoint to search for student by registration number"""
    
    if request.method == 'GET':
        reg_number = request.GET.get('reg_number', '').strip()
        
        if not reg_number:
            return JsonResponse({'error': 'Registration number is required'}, status=400)
        
        try:
            student = Student.objects.select_related(
                'user', 'programme'
            ).get(registration_number__iexact=reg_number)
            
            return JsonResponse({
                'success': True,
                'student': {
                    'id': student.user_id,
                    'registration_number': student.registration_number,
                    'full_name': f"{student.first_name} {student.last_name}",
                    'email': student.email or student.user.email,
                    'programme': student.programme.name,
                    'programme_code': student.programme.code,
                    'current_year': student.current_year,
                }
            })
            
        except Student.DoesNotExist:
            return JsonResponse({
                'error': 'Student not found with this registration number'
            }, status=404)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@user_passes_test(is_admin_or_staff)
def student_units_view(request, student_id, semester_id):
    """View to display and enter marks for student's enrolled units"""
    
    student = get_object_or_404(
        Student.objects.select_related('user', 'programme'),
        user_id=student_id
    )
    
    semester = get_object_or_404(
        Semester.objects.select_related('academic_year'),
        id=semester_id
    )
    
    # Get all enrollments for this student in this semester
    enrollments = UnitEnrollment.objects.filter(
        student=student,
        semester=semester
    ).select_related(
        'unit'
    ).prefetch_related(
        'marks__assessment_component'
    ).order_by('unit__code')
    
    # Get the lecturer (if current user is a lecturer)
    lecturer = None
    try:
        if hasattr(request.user, 'lecturer_profile'):
            lecturer = request.user.lecturer_profile
    except:
        pass
    
    # Prepare enrollment data with assessments
    enrollment_data = []
    for enrollment in enrollments:
        # Get all assessment components for this unit
        assessment_components = AssessmentComponent.objects.filter(
            unit=enrollment.unit
        ).order_by('component_type')
        
        # Get marks for this enrollment
        marks_dict = {}
        for mark in enrollment.marks.all():
            marks_dict[mark.assessment_component.id] = mark
        
        # Calculate total marks
        total_marks = Decimal('0.00')
        total_weight = Decimal('0.00')
        
        assessment_list = []
        for component in assessment_components:
            mark_obj = marks_dict.get(component.id)
            
            # Calculate weighted score
            weighted_score = None
            if mark_obj and mark_obj.marks_obtained is not None:
                percentage = (mark_obj.marks_obtained / component.max_marks) * 100
                weighted_score = (percentage * component.weight_percentage) / 100
                total_marks += weighted_score
            
            total_weight += component.weight_percentage
            
            assessment_list.append({
                'component': component,
                'mark': mark_obj,
                'weighted_score': weighted_score
            })
        
        # Check if final grade exists
        try:
            final_grade = enrollment.final_grade
        except:
            final_grade = None
        
        enrollment_data.append({
            'enrollment': enrollment,
            'assessments': assessment_list,
            'total_marks': round(total_marks, 2),
            'total_weight': total_weight,
            'final_grade': final_grade,
            'has_all_marks': all(a['mark'] is not None and a['mark'].marks_obtained is not None for a in assessment_list)
        })
    
    # Get grading scheme for this programme
    grading_scheme = GradingScheme.objects.filter(
        programme=student.programme
    ).order_by('-min_marks')
    
    context = {
        'student': student,
        'semester': semester,
        'enrollment_data': enrollment_data,
        'grading_scheme': grading_scheme,
        'lecturer': lecturer,
    }
    
    return render(request, 'admin/student_marks_entry.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def save_marks_ajax(request):
    """AJAX endpoint to save marks for a specific assessment"""
    
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        component_id = request.POST.get('component_id')
        marks = request.POST.get('marks')
        
        if not all([enrollment_id, component_id]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        try:
            enrollment = UnitEnrollment.objects.get(id=enrollment_id)
            component = AssessmentComponent.objects.get(id=component_id)
            
            # Handle empty marks (delete existing)
            if marks == '' or marks is None:
                StudentMarks.objects.filter(
                    enrollment=enrollment,
                    assessment_component=component
                ).delete()
                return JsonResponse({
                    'success': True,
                    'message': 'Marks cleared successfully',
                    'weighted_score': None
                })
            
            marks = Decimal(marks)
            
            # Validate marks
            if marks < 0 or marks > component.max_marks:
                return JsonResponse({
                    'error': f'Marks must be between 0 and {component.max_marks}'
                }, status=400)
            
            # Get or create lecturer
            lecturer = None
            try:
                if hasattr(request.user, 'lecturer_profile'):
                    lecturer = request.user.lecturer_profile
                else:
                    # Get any lecturer as fallback
                    lecturer = Lecturer.objects.first()
            except:
                lecturer = Lecturer.objects.first()
            
            if not lecturer:
                return JsonResponse({'error': 'No lecturer found in system'}, status=400)
            
            # Create or update marks
            mark_obj, created = StudentMarks.objects.update_or_create(
                enrollment=enrollment,
                assessment_component=component,
                defaults={
                    'marks_obtained': marks,
                    'entered_by': lecturer
                }
            )
            
            # Calculate weighted score
            percentage = (marks / component.max_marks) * 100
            weighted_score = (percentage * component.weight_percentage) / 100
            
            return JsonResponse({
                'success': True,
                'message': 'Marks saved successfully',
                'weighted_score': float(round(weighted_score, 2)),
                'created': created
            })
            
        except (UnitEnrollment.DoesNotExist, AssessmentComponent.DoesNotExist):
            return JsonResponse({'error': 'Enrollment or Assessment Component not found'}, status=404)
        except (ValueError, InvalidOperation) as e:
            return JsonResponse({'error': f'Invalid marks value: {str(e)}'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@user_passes_test(is_admin_or_staff)
def calculate_final_grade_ajax(request):
    """AJAX endpoint to calculate and save final grade for an enrollment"""
    
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        
        if not enrollment_id:
            return JsonResponse({'error': 'Enrollment ID is required'}, status=400)
        
        try:
            enrollment = UnitEnrollment.objects.select_related('unit', 'student__programme').get(id=enrollment_id)
            
            # Get all assessment components for this unit
            components = AssessmentComponent.objects.filter(unit=enrollment.unit)
            
            if not components.exists():
                return JsonResponse({'error': 'No assessment components defined for this unit'}, status=400)
            
            # Check if all components have marks
            marks = StudentMarks.objects.filter(
                enrollment=enrollment,
                assessment_component__in=components
            )
            
            if marks.count() != components.count():
                return JsonResponse({
                    'error': 'Not all assessment components have been graded'
                }, status=400)
            
            # Calculate total marks (weighted)
            total_marks = Decimal('0.00')
            
            for mark in marks:
                component = mark.assessment_component
                percentage = (mark.marks_obtained / component.max_marks) * 100
                weighted_score = (percentage * component.weight_percentage) / 100
                total_marks += weighted_score
            
            # Determine grade based on grading scheme
            grading_scheme = GradingScheme.objects.filter(
                programme=enrollment.student.programme,
                min_marks__lte=total_marks,
                max_marks__gte=total_marks
            ).first()
            
            if not grading_scheme:
                return JsonResponse({'error': 'No matching grade found in grading scheme'}, status=400)
            
            # Get or create lecturer
            lecturer = None
            try:
                if hasattr(request.user, 'lecturer_profile'):
                    lecturer = request.user.lecturer_profile
            except:
                pass
            
            # Create or update final grade
            final_grade, created = FinalGrade.objects.update_or_create(
                enrollment=enrollment,
                defaults={
                    'total_marks': total_marks,
                    'grade': grading_scheme.grade,
                    'grade_point': grading_scheme.grade_point,
                    'approved_by': lecturer,
                    'is_approved': True
                }
            )
            
            # Update enrollment status
            enrollment.status = 'COMPLETED'
            enrollment.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Final grade calculated successfully',
                'total_marks': float(round(total_marks, 2)),
                'grade': grading_scheme.grade,
                'grade_point': float(grading_scheme.grade_point),
                'description': grading_scheme.description
            })
            
        except UnitEnrollment.DoesNotExist:
            return JsonResponse({'error': 'Enrollment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error calculating grade: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@user_passes_test(is_admin_or_staff)
def bulk_marks_entry_view(request, semester_id, unit_id):
    """View for entering marks for all students in a unit at once"""
    
    semester = get_object_or_404(
        Semester.objects.select_related('academic_year'),
        id=semester_id
    )
    
    unit = get_object_or_404(Unit, id=unit_id)
    
    # Get all enrollments for this unit in this semester
    enrollments = UnitEnrollment.objects.filter(
        semester=semester,
        unit=unit,
        status__in=['ENROLLED', 'COMPLETED']
    ).select_related(
        'student__user',
        'student__programme'
    ).prefetch_related(
        'marks__assessment_component'
    ).order_by('student__registration_number')
    
    # Get assessment components for this unit
    components = AssessmentComponent.objects.filter(
        unit=unit
    ).order_by('component_type')
    
    # Prepare data
    student_data = []
    for enrollment in enrollments:
        marks_dict = {}
        for mark in enrollment.marks.all():
            marks_dict[mark.assessment_component.id] = mark.marks_obtained
        
        # Get final grade if exists
        try:
            final_grade = enrollment.final_grade
        except:
            final_grade = None
        
        student_data.append({
            'enrollment': enrollment,
            'student': enrollment.student,
            'marks': marks_dict,
            'final_grade': final_grade
        })
    
    context = {
        'semester': semester,
        'unit': unit,
        'components': components,
        'student_data': student_data,
    }
    
    return render(request, 'admin/bulk_marks_entry.html', context)