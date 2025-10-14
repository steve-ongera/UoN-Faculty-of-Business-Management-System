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