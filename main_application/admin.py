from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import (
    User, AcademicYear, Semester, Intake, Department, Programme, Unit,
    ProgrammeUnit, Student, StudentProgression, UnitEnrollment, SemesterRegistration,
    Lecturer, UnitAllocation, GradingScheme, AssessmentComponent, StudentMarks,
    FinalGrade, Venue, TimetableSlot, FeeStructure, FeePayment, FeeStatement,
    Announcement, Event, EventRegistration, Message, MessageReadStatus
)


# ========================
# CUSTOM USER ADMIN
# ========================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'user_type', 'is_active_user', 'is_staff'
    )
    list_filter = ('user_type', 'is_active_user', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('username',)

    # 👇 Remove the default date_joined field completely
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Custom Fields', {'fields': ('user_type', 'is_active_user')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name', 'password1', 'password2',
                'user_type', 'phone_number', 'profile_picture', 'is_active_user',
            ),
        }),
    )

    exclude = ('date_joined',)  # 👈 ensure admin doesn’t try to access it


# ========================
# ACADEMIC STRUCTURE
# ========================

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year_code', 'start_date', 'end_date', 'is_current', 'created_at')
    list_filter = ('is_current',)
    search_fields = ('year_code',)
    date_hierarchy = 'start_date'
    
    def save_model(self, request, obj, form, change):
        if obj.is_current:
            # Ensure only one academic year is current
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save_model(request, obj, form, change)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'academic_year', 'semester_number', 'start_date', 'end_date', 
                    'is_current', 'registration_deadline')
    list_filter = ('is_current', 'semester_number', 'academic_year')
    search_fields = ('academic_year__year_code',)
    date_hierarchy = 'start_date'
    
    def save_model(self, request, obj, form, change):
        if obj.is_current:
            # Ensure only one semester is current
            Semester.objects.filter(is_current=True).update(is_current=False)
        super().save_model(request, obj, form, change)


@admin.register(Intake)
class IntakeAdmin(admin.ModelAdmin):
    list_display = ('name', 'intake_type', 'academic_year', 'intake_date', 'is_active')
    list_filter = ('intake_type', 'is_active', 'academic_year')
    search_fields = ('name',)
    date_hierarchy = 'intake_date'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'head_of_department', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'code')
    raw_id_fields = ('head_of_department',)


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'level', 'department', 'duration_years', 
                    'semesters_per_year', 'is_active')
    list_filter = ('level', 'is_active', 'department', 'duration_years', 'semesters_per_year')
    search_fields = ('name', 'code')
    date_hierarchy = 'created_at'


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credit_hours', 'department', 'is_core', 'created_at')
    list_filter = ('is_core', 'department', 'credit_hours')
    search_fields = ('code', 'name')
    filter_horizontal = ('prerequisites',)
    date_hierarchy = 'created_at'


@admin.register(ProgrammeUnit)
class ProgrammeUnitAdmin(admin.ModelAdmin):
    list_display = ('programme', 'unit', 'year_level', 'semester', 'is_mandatory')
    list_filter = ('programme', 'year_level', 'semester', 'is_mandatory')
    search_fields = ('programme__name', 'unit__name', 'unit__code')
    raw_id_fields = ('programme', 'unit')


# ========================
# STUDENT MANAGEMENT
# ========================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'get_full_name', 'programme', 'current_year', 
                    'intake', 'is_active', 'admission_date')
    list_filter = ('is_active', 'current_year', 'programme', 'intake', 'can_upgrade')
    search_fields = ('registration_number', 'first_name', 'last_name', 'surname', 
                     'user__username', 'email', 'phone')
    date_hierarchy = 'admission_date'
    raw_id_fields = ('user', 'programme', 'intake')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'registration_number', 'first_name', 'last_name', 'surname')
        }),
        ('Academic Information', {
            'fields': ('programme', 'current_year', 'intake', 'admission_date', 'is_active', 'can_upgrade')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'date_of_birth', 'address')
        }),
        ('Parent/Guardian Information', {
            'fields': ('parent_name', 'parent_phone', 'guardian_name', 'guardian_phone')
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name} {obj.surname or ''}".strip()
    get_full_name.short_description = 'Full Name'


@admin.register(StudentProgression)
class StudentProgressionAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_programme', 'to_programme', 'completion_date', 'upgrade_date')
    list_filter = ('from_programme', 'to_programme', 'completion_date')
    search_fields = ('student__registration_number', 'student__first_name', 'student__last_name')
    date_hierarchy = 'completion_date'
    raw_id_fields = ('student', 'from_programme', 'to_programme')


@admin.register(UnitEnrollment)
class UnitEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'unit', 'semester', 'status', 'enrollment_date')
    list_filter = ('status', 'semester', 'unit__department')
    search_fields = ('student__registration_number', 'unit__code', 'unit__name')
    date_hierarchy = 'enrollment_date'
    raw_id_fields = ('student', 'unit', 'semester')


@admin.register(SemesterRegistration)
class SemesterRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'status', 'units_enrolled', 'registration_date')
    list_filter = ('status', 'semester')
    search_fields = ('student__registration_number',)
    date_hierarchy = 'registration_date'
    raw_id_fields = ('student', 'semester')


# ========================
# LECTURER MANAGEMENT
# ========================

@admin.register(Lecturer)
class LecturerAdmin(admin.ModelAdmin):
    list_display = ('staff_number', 'get_full_name', 'department', 'specialization', 
                    'office_location', 'is_active')
    list_filter = ('is_active', 'department')
    search_fields = ('staff_number', 'user__first_name', 'user__last_name', 
                     'specialization', 'office_location')
    raw_id_fields = ('user', 'department')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(UnitAllocation)
class UnitAllocationAdmin(admin.ModelAdmin):
    list_display = ('unit', 'lecturer', 'semester', 'is_active', 'allocated_date')
    list_filter = ('is_active', 'semester', 'unit__department')
    search_fields = ('unit__code', 'unit__name', 'lecturer__staff_number')
    date_hierarchy = 'allocated_date'
    raw_id_fields = ('unit', 'lecturer', 'semester')
    filter_horizontal = ('programmes',)


# ========================
# GRADING & ASSESSMENT
# ========================

@admin.register(GradingScheme)
class GradingSchemeAdmin(admin.ModelAdmin):
    list_display = ('programme', 'grade', 'min_marks', 'max_marks', 'grade_point', 'description')
    list_filter = ('programme',)
    search_fields = ('programme__code', 'programme__name', 'grade')


@admin.register(AssessmentComponent)
class AssessmentComponentAdmin(admin.ModelAdmin):
    list_display = ('unit', 'name', 'component_type', 'weight_percentage', 'max_marks')
    list_filter = ('component_type', 'unit__department')
    search_fields = ('name', 'unit__code', 'unit__name')
    raw_id_fields = ('unit',)


@admin.register(StudentMarks)
class StudentMarksAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'get_unit', 'assessment_component', 'marks_obtained', 
                    'entered_by', 'entry_date')
    list_filter = ('assessment_component__component_type', 'entry_date', 'entered_by')
    search_fields = ('enrollment__student__registration_number', 
                     'enrollment__unit__code', 'assessment_component__name')
    date_hierarchy = 'entry_date'
    raw_id_fields = ('enrollment', 'assessment_component', 'entered_by')
    
    def get_student(self, obj):
        return obj.enrollment.student.registration_number
    get_student.short_description = 'Student'
    
    def get_unit(self, obj):
        return obj.enrollment.unit.code
    get_unit.short_description = 'Unit'


@admin.register(FinalGrade)
class FinalGradeAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'get_unit', 'total_marks', 'grade', 'grade_point', 
                    'is_approved', 'approved_by', 'computed_date')
    list_filter = ('is_approved', 'grade', 'computed_date')
    search_fields = ('enrollment__student__registration_number', 'enrollment__unit__code', 'grade')
    date_hierarchy = 'computed_date'
    raw_id_fields = ('enrollment', 'approved_by')
    
    def get_student(self, obj):
        return obj.enrollment.student.registration_number
    get_student.short_description = 'Student'
    
    def get_unit(self, obj):
        return obj.enrollment.unit.code
    get_unit.short_description = 'Unit'


# ========================
# TIMETABLING
# ========================

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'venue_type', 'capacity', 'building', 'floor', 
                    'has_projector', 'has_computers', 'is_available')
    list_filter = ('venue_type', 'is_available', 'has_projector', 'has_computers', 'building')
    search_fields = ('name', 'code', 'building')


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ('get_unit', 'get_lecturer', 'day_of_week', 'start_time', 'end_time', 
                    'venue', 'programme', 'year_level', 'is_active')
    list_filter = ('day_of_week', 'is_active', 'programme', 'year_level', 'venue')
    search_fields = ('unit_allocation__unit__code', 'unit_allocation__lecturer__staff_number', 
                     'venue__code')
    date_hierarchy = 'created_at'
    raw_id_fields = ('unit_allocation', 'venue', 'programme', 'created_by')
    
    def get_unit(self, obj):
        return obj.unit_allocation.unit.code
    get_unit.short_description = 'Unit'
    
    def get_lecturer(self, obj):
        return obj.unit_allocation.lecturer.staff_number
    get_lecturer.short_description = 'Lecturer'


# ========================
# FEES MANAGEMENT
# ========================

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('programme', 'academic_year', 'year_level', 'tuition_fee', 
                    'examination_fee', 'registration_fee', 'other_fees', 'total_fee')
    list_filter = ('programme', 'academic_year', 'year_level')
    search_fields = ('programme__code', 'programme__name')
    raw_id_fields = ('programme', 'academic_year')


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'receipt_number', 'amount_paid', 'payment_date', 
                    'payment_method', 'status', 'balance', 'semester')
    list_filter = ('status', 'payment_method', 'payment_date', 'semester')
    search_fields = ('student__registration_number', 'receipt_number')
    date_hierarchy = 'payment_date'
    raw_id_fields = ('student', 'semester', 'fee_structure')


@admin.register(FeeStatement)
class FeeStatementAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'total_billed', 'total_paid', 'balance', 
                    'can_register', 'last_updated')
    list_filter = ('can_register', 'semester')
    search_fields = ('student__registration_number',)
    date_hierarchy = 'last_updated'
    raw_id_fields = ('student', 'semester')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ('total_billed', 'total_paid', 'balance', 'last_updated')
        return ()


# ========================
# COMMUNICATION
# ========================

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'created_by', 'publish_date', 'expiry_date', 
                    'is_published', 'created_at')
    list_filter = ('priority', 'is_published', 'publish_date', 'created_by')
    search_fields = ('title', 'content')
    date_hierarchy = 'publish_date'
    filter_horizontal = ('target_programmes',)
    raw_id_fields = ('created_by',)
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'attachments')
        }),
        ('Targeting', {
            'fields': ('target_programmes', 'target_year_levels')
        }),
        ('Publishing', {
            'fields': ('priority', 'publish_date', 'expiry_date', 'is_published', 'created_by')
        }),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'event_date', 'start_time', 'end_time', 
                    'venue', 'organizer', 'is_mandatory', 'registration_required')
    list_filter = ('event_type', 'is_mandatory', 'registration_required', 'event_date')
    search_fields = ('title', 'description')
    date_hierarchy = 'event_date'
    filter_horizontal = ('target_programmes',)
    raw_id_fields = ('venue', 'organizer')


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'student', 'registration_date', 'attended')
    list_filter = ('attended', 'event', 'registration_date')
    search_fields = ('event__title', 'student__registration_number')
    date_hierarchy = 'registration_date'
    raw_id_fields = ('event', 'student')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'subject', 'message_type', 'sent_at', 'get_recipient_count')
    list_filter = ('message_type', 'sent_at')
    search_fields = ('subject', 'body', 'sender__username')
    date_hierarchy = 'sent_at'
    filter_horizontal = ('recipients',)
    raw_id_fields = ('sender', 'parent_message')
    
    def get_recipient_count(self, obj):
        return obj.recipients.count()
    get_recipient_count.short_description = 'Recipients'


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ('message', 'recipient', 'is_read', 'read_at')
    list_filter = ('is_read', 'read_at')
    search_fields = ('message__subject', 'recipient__username')
    date_hierarchy = 'read_at'
    raw_id_fields = ('message', 'recipient')



from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from django.contrib.admin import SimpleListFilter
import json

from .models import (
    AuditLog, SecurityEvent, LoginAttempt, UserSession, SystemSettings,
    BlockedIP, DataExportLog, ChatbotConversation, ChatMessage,
    MentalHealthAssessment, ChatbotKnowledgeBase, ChatbotIntent,
    ChatbotFeedback, CrisisAlert, ChatbotAnalytics
)


# ========================
# CUSTOM FILTERS
# ========================

class SeverityFilter(SimpleListFilter):
    title = 'severity level'
    parameter_name = 'severity'

    def lookups(self, request, model_admin):
        return (
            ('HIGH', 'High & Critical'),
            ('MEDIUM', 'Medium'),
            ('LOW', 'Low'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'HIGH':
            return queryset.filter(severity__in=['HIGH', 'CRITICAL'])
        if self.value():
            return queryset.filter(severity=self.value())


class DateRangeFilter(SimpleListFilter):
    title = 'date range'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('year', 'This Year'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(timestamp__date=now.date())
        if self.value() == 'week':
            return queryset.filter(timestamp__gte=now - timezone.timedelta(days=7))
        if self.value() == 'month':
            return queryset.filter(timestamp__gte=now - timezone.timedelta(days=30))
        if self.value() == 'year':
            return queryset.filter(timestamp__gte=now - timezone.timedelta(days=365))


# ========================
# SECURITY & AUDIT TRAIL ADMIN
# ========================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'user_type_display', 'action_type', 
                    'model_name', 'severity_badge', 'ip_address']
    list_filter = ['action_type', 'severity', 'user_type', DateRangeFilter]
    search_fields = ['username', 'action_description', 'ip_address', 'object_repr']
    readonly_fields = ['timestamp', 'user', 'username', 'user_type', 'action_type',
                       'action_description', 'content_type', 'object_id', 'model_name',
                       'object_repr', 'old_values_display', 'new_values_display', 
                       'changes_summary', 'ip_address', 'user_agent', 'request_path',
                       'request_method', 'severity', 'is_suspicious']
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'username', 'user_type')
        }),
        ('Action Details', {
            'fields': ('action_type', 'action_description', 'model_name', 'object_repr')
        }),
        ('Object Reference', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Changes', {
            'fields': ('old_values_display', 'new_values_display', 'changes_summary'),
            'classes': ('collapse',)
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'request_path', 'request_method'),
            'classes': ('collapse',)
        }),
        ('Security', {
            'fields': ('severity', 'is_suspicious', 'timestamp')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def user_type_display(self, obj):
        return obj.user_type or 'N/A'
    user_type_display.short_description = 'User Type'
    
    def severity_badge(self, obj):
        colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.severity, '#6c757d'),
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Severity'
    
    def old_values_display(self, obj):
        if obj.old_values:
            return format_html('<pre>{}</pre>', json.dumps(obj.old_values, indent=2))
        return 'N/A'
    old_values_display.short_description = 'Old Values'
    
    def new_values_display(self, obj):
        if obj.new_values:
            return format_html('<pre>{}</pre>', json.dumps(obj.new_values, indent=2))
        return 'N/A'
    new_values_display.short_description = 'New Values'


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['detected_at', 'event_type', 'risk_badge', 'status_badge', 
                    'username', 'ip_address', 'auto_blocked']
    list_filter = ['event_type', 'risk_level', 'status', 'auto_blocked', DateRangeFilter]
    search_fields = ['username', 'description', 'ip_address']
    readonly_fields = ['detected_at']
    date_hierarchy = 'detected_at'
    list_per_page = 50
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'risk_level', 'status', 'description')
        }),
        ('User Details', {
            'fields': ('user', 'username', 'ip_address', 'user_agent')
        }),
        ('Request Information', {
            'fields': ('request_path', 'request_data'),
            'classes': ('collapse',)
        }),
        ('Event Details', {
            'fields': ('details_display',),
            'classes': ('collapse',)
        }),
        ('Response & Resolution', {
            'fields': ('action_taken', 'resolved_by', 'resolved_at', 
                      'auto_blocked', 'block_duration_minutes')
        }),
        ('Timestamps', {
            'fields': ('detected_at',)
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_false_positive', 'block_ip_addresses']
    
    def risk_badge(self, obj):
        colors = {
            'LOW': '#17a2b8',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.risk_level, '#6c757d'),
            obj.get_risk_level_display()
        )
    risk_badge.short_description = 'Risk Level'
    
    def status_badge(self, obj):
        colors = {
            'DETECTED': '#ffc107',
            'INVESTIGATING': '#17a2b8',
            'RESOLVED': '#28a745',
            'FALSE_POSITIVE': '#6c757d',
            'IGNORED': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def details_display(self, obj):
        if obj.details:
            return format_html('<pre>{}</pre>', json.dumps(obj.details, indent=2))
        return 'N/A'
    details_display.short_description = 'Event Details'
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(
            status='RESOLVED',
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f'{updated} security event(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark selected as resolved'
    
    def mark_as_false_positive(self, request, queryset):
        updated = queryset.update(status='FALSE_POSITIVE', resolved_at=timezone.now())
        self.message_user(request, f'{updated} security event(s) marked as false positive.')
    mark_as_false_positive.short_description = 'Mark as false positive'
    
    def block_ip_addresses(self, request, queryset):
        blocked_count = 0
        for event in queryset:
            if event.ip_address:
                BlockedIP.objects.get_or_create(
                    ip_address=event.ip_address,
                    defaults={
                        'reason': 'AUTOMATED_BLOCK',
                        'description': f'Auto-blocked due to security event: {event.event_type}',
                        'blocked_by': request.user
                    }
                )
                blocked_count += 1
        self.message_user(request, f'{blocked_count} IP address(es) blocked.')
    block_ip_addresses.short_description = 'Block IP addresses'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'success_badge', 'ip_address', 
                    'country', 'user_agent_short']
    list_filter = ['success', DateRangeFilter]
    search_fields = ['username', 'ip_address', 'country', 'city']
    readonly_fields = ['timestamp', 'username', 'user', 'success', 'failure_reason',
                       'ip_address', 'user_agent', 'country', 'city', 'session_key']
    date_hierarchy = 'timestamp'
    list_per_page = 100
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def success_badge(self, obj):
        if obj.success:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Success</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Failed</span>'
        )
    success_badge.short_description = 'Status'
    
    def user_agent_short(self, obj):
        return obj.user_agent[:50] + '...' if len(obj.user_agent) > 50 else obj.user_agent
    user_agent_short.short_description = 'User Agent'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'last_activity', 'is_active_badge', 
                    'ip_address', 'device_type', 'browser']
    list_filter = ['is_active', 'device_type', DateRangeFilter]
    search_fields = ['user__username', 'ip_address', 'session_key']
    readonly_fields = ['session_key', 'login_time', 'last_activity']
    date_hierarchy = 'login_time'
    list_per_page = 50
    
    actions = ['terminate_sessions']
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'
    
    def terminate_sessions(self, request, queryset):
        updated = queryset.update(
            is_active=False,
            logout_time=timezone.now()
        )
        self.message_user(request, f'{updated} session(s) terminated.')
    terminate_sessions.short_description = 'Terminate selected sessions'


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['id', 'maintenance_mode_badge', 'updated_at', 'updated_by']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Maintenance Mode', {
            'fields': ('maintenance_mode', 'maintenance_message', 
                      'maintenance_started_at', 'maintenance_started_by'),
            'classes': ('wide',)
        }),
        ('Security Settings', {
            'fields': ('max_login_attempts', 'lockout_duration_minutes',
                      'session_timeout_minutes', 'require_password_change_days'),
            'classes': ('wide',)
        }),
        ('Rate Limiting', {
            'fields': ('enable_rate_limiting', 'api_rate_limit_per_minute'),
            'classes': ('wide',)
        }),
        ('Audit Settings', {
            'fields': ('enable_audit_logging', 'audit_log_retention_days', 
                      'log_view_actions'),
            'classes': ('wide',)
        }),
        ('Advanced Security', {
            'fields': ('enable_two_factor_auth', 'enable_ip_whitelist', 'whitelist_ips'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('security_alert_emails',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings record
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def maintenance_mode_badge(self, obj):
        if obj.maintenance_mode:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;">🔧 MAINTENANCE ON</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 5px 15px; border-radius: 3px;">✓ Active</span>'
        )
    maintenance_mode_badge.short_description = 'Status'


@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'reason', 'is_active_badge', 'blocked_at', 
                    'blocked_until', 'block_count']
    list_filter = ['reason', 'is_active', DateRangeFilter]
    search_fields = ['ip_address', 'description']
    readonly_fields = ['blocked_at', 'unblocked_at']
    date_hierarchy = 'blocked_at'
    
    actions = ['unblock_ips', 'make_permanent']
    
    fieldsets = (
        ('IP Information', {
            'fields': ('ip_address', 'reason', 'description')
        }),
        ('Block Details', {
            'fields': ('blocked_at', 'blocked_by', 'blocked_until', 'block_count')
        }),
        ('Status', {
            'fields': ('is_active', 'unblocked_at', 'unblocked_by')
        }),
    )
    
    def is_active_badge(self, obj):
        if obj.is_blocked():
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">🚫 Blocked</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Unblocked</span>'
        )
    is_active_badge.short_description = 'Status'
    
    def unblock_ips(self, request, queryset):
        updated = queryset.update(
            is_active=False,
            unblocked_at=timezone.now(),
            unblocked_by=request.user
        )
        self.message_user(request, f'{updated} IP address(es) unblocked.')
    unblock_ips.short_description = 'Unblock selected IPs'
    
    def make_permanent(self, request, queryset):
        updated = queryset.update(blocked_until=None)
        self.message_user(request, f'{updated} block(s) made permanent.')
    make_permanent.short_description = 'Make blocks permanent'


@admin.register(DataExportLog)
class DataExportLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'export_type', 'record_count', 
                    'file_format', 'file_size_display', 'ip_address']
    list_filter = ['export_type', 'file_format', DateRangeFilter]
    search_fields = ['user__username', 'export_type', 'ip_address']
    readonly_fields = ['timestamp', 'user', 'export_type', 'model_name', 'record_count',
                       'filters_applied_display', 'fields_exported_display', 
                       'file_format', 'file_size_bytes', 'ip_address', 'approved_by']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def file_size_display(self, obj):
        if obj.file_size_bytes:
            size_mb = obj.file_size_bytes / (1024 * 1024)
            if size_mb < 1:
                return f"{obj.file_size_bytes / 1024:.2f} KB"
            return f"{size_mb:.2f} MB"
        return 'N/A'
    file_size_display.short_description = 'File Size'
    
    def filters_applied_display(self, obj):
        if obj.filters_applied:
            return format_html('<pre>{}</pre>', json.dumps(obj.filters_applied, indent=2))
        return 'No filters'
    filters_applied_display.short_description = 'Filters Applied'
    
    def fields_exported_display(self, obj):
        if obj.fields_exported:
            return format_html('<pre>{}</pre>', json.dumps(obj.fields_exported, indent=2))
        return 'All fields'
    fields_exported_display.short_description = 'Fields Exported'


# ========================
# AI CHATBOT SYSTEM ADMIN
# ========================

@admin.register(ChatbotConversation)
class ChatbotConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id_short', 'user', 'conversation_type', 
                    'status_badge', 'sentiment_badge', 'started_at', 
                    'total_messages', 'escalated']
    list_filter = ['conversation_type', 'status', 'overall_sentiment', 
                   'escalated', DateRangeFilter]
    search_fields = ['conversation_id', 'user__username', 'student__registration_number', 'title']
    readonly_fields = ['conversation_id', 'started_at', 'last_message_at', 'closed_at',
                       'total_messages', 'ai_responses', 'user_messages', 
                       'avg_response_time_seconds', 'escalated_at']
    date_hierarchy = 'started_at'
    list_per_page = 50
    
    fieldsets = (
        ('Conversation Info', {
            'fields': ('conversation_id', 'user', 'student', 'conversation_type', 'title')
        }),
        ('Status & Sentiment', {
            'fields': ('status', 'overall_sentiment', 'user_satisfaction', 'user_feedback')
        }),
        ('Metrics', {
            'fields': ('total_messages', 'ai_responses', 'user_messages', 
                      'avg_response_time_seconds'),
            'classes': ('collapse',)
        }),
        ('Escalation', {
            'fields': ('escalated', 'escalated_at', 'escalated_to', 'escalation_reason'),
            'classes': ('collapse',)
        }),
        ('Session Info', {
            'fields': ('ip_address', 'user_agent', 'device_type'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'last_message_at', 'closed_at')
        }),
    )
    
    actions = ['close_conversations', 'escalate_conversations']
    
    def conversation_id_short(self, obj):
        return str(obj.conversation_id)[:8]
    conversation_id_short.short_description = 'ID'
    
    def status_badge(self, obj):
        colors = {
            'ACTIVE': '#28a745',
            'CLOSED': '#6c757d',
            'ESCALATED': '#dc3545',
            'ARCHIVED': '#17a2b8'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def sentiment_badge(self, obj):
        colors = {
            'POSITIVE': '#28a745',
            'NEUTRAL': '#17a2b8',
            'NEGATIVE': '#ffc107',
            'CRISIS': '#dc3545'
        }
        icons = {
            'POSITIVE': '😊',
            'NEUTRAL': '😐',
            'NEGATIVE': '😟',
            'CRISIS': '🚨'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.overall_sentiment, '#6c757d'),
            icons.get(obj.overall_sentiment, ''),
            obj.get_overall_sentiment_display()
        )
    sentiment_badge.short_description = 'Sentiment'
    
    def close_conversations(self, request, queryset):
        for conv in queryset:
            conv.close_conversation()
        self.message_user(request, f'{queryset.count()} conversation(s) closed.')
    close_conversations.short_description = 'Close selected conversations'
    
    def escalate_conversations(self, request, queryset):
        for conv in queryset.filter(escalated=False):
            conv.escalate(reason='Escalated by admin', escalated_to=request.user)
        self.message_user(request, 'Selected conversations escalated.')
    escalate_conversations.short_description = 'Escalate to human support'


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    max_num = 0
    fields = ['message_type', 'content_preview', 'sentiment', 'is_crisis', 'created_at']
    readonly_fields = ['message_type', 'content_preview', 'sentiment', 'is_crisis', 'created_at']
    can_delete = False
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['message_id_short', 'conversation_link', 'message_type', 
                    'sentiment_badge', 'crisis_badge', 'created_at', 'was_helpful']
    list_filter = ['message_type', 'sentiment', 'is_crisis', DateRangeFilter]
    search_fields = ['message_id', 'content', 'conversation__user__username']
    readonly_fields = ['message_id', 'created_at', 'processed_content', 
                       'intent_detected', 'entities_display', 'confidence_score',
                       'sentiment_score', 'emotion_scores_display', 'crisis_keywords_display']
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    fieldsets = (
        ('Message Info', {
            'fields': ('message_id', 'conversation', 'message_type', 'content')
        }),
        ('AI Processing', {
            'fields': ('processed_content', 'intent_detected', 'entities_display', 
                      'confidence_score', 'model_used', 'tokens_used', 'response_time_seconds'),
            'classes': ('collapse',)
        }),
        ('Sentiment Analysis', {
            'fields': ('sentiment', 'sentiment_score', 'emotion_scores_display'),
            'classes': ('collapse',)
        }),
        ('Crisis Detection', {
            'fields': ('is_crisis', 'crisis_keywords_display', 'crisis_level'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('was_helpful', 'feedback_text'),
            'classes': ('collapse',)
        }),
        ('Attachment', {
            'fields': ('has_attachment', 'attachment'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def message_id_short(self, obj):
        return str(obj.message_id)[:8]
    message_id_short.short_description = 'ID'
    
    def conversation_link(self, obj):
        url = reverse('admin:main_application_chatbotconversation_change', args=[obj.conversation.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.conversation.conversation_id)[:8])
    conversation_link.short_description = 'Conversation'
    
    def sentiment_badge(self, obj):
        colors = {
            'POSITIVE': '#28a745',
            'NEUTRAL': '#17a2b8',
            'NEGATIVE': '#ffc107',
            'ANXIOUS': '#fd7e14',
            'DEPRESSED': '#dc3545',
            'CRISIS': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.sentiment, '#6c757d'),
            obj.get_sentiment_display()
        )
    sentiment_badge.short_description = 'Sentiment'
    
    def crisis_badge(self, obj):
        if obj.is_crisis:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🚨 CRISIS</span>'
            )
        return '-'
    crisis_badge.short_description = 'Crisis'
    
    def entities_display(self, obj):
        if obj.entities_extracted:
            return format_html('<pre>{}</pre>', json.dumps(obj.entities_extracted, indent=2))
        return 'None'
    entities_display.short_description = 'Entities Extracted'
    
    def emotion_scores_display(self, obj):
        if obj.emotion_scores:
            return format_html('<pre>{}</pre>', json.dumps(obj.emotion_scores, indent=2))
        return 'N/A'
    emotion_scores_display.short_description = 'Emotion Scores'
    
    def crisis_keywords_display(self, obj):
        if obj.crisis_keywords:
            return format_html('<pre>{}</pre>', json.dumps(obj.crisis_keywords, indent=2))
        return 'None'
    crisis_keywords_display.short_description = 'Crisis Keywords'


@admin.register(MentalHealthAssessment)
class MentalHealthAssessmentAdmin(admin.ModelAdmin):
    list_display = ['assessment_id_short', 'student', 'assessment_type', 
                    'risk_badge', 'score_display', 'assessed_at', 
                    'requires_followup', 'professional_referral_recommended']
    list_filter = ['assessment_type', 'risk_level', 'requires_followup', 
                   'professional_referral_recommended', 'followup_completed', DateRangeFilter]
    search_fields = ['assessment_id', 'student__registration_number', 'student__user__username']
    readonly_fields = ['assessment_id', 'assessed_at', 'responses_display']
    date_hierarchy = 'assessed_at'
    
    fieldsets = (
        ('Assessment Info', {
            'fields': ('assessment_id', 'student', 'conversation', 'assessment_type')
        }),
        ('Results', {
            'fields': ('score', 'max_score', 'risk_level', 'interpretation', 'recommendations')
        }),
        ('Detailed Responses', {
            'fields': ('responses_display',),
            'classes': ('collapse',)
        }),
        ('Follow-up', {
            'fields': ('requires_followup', 'followup_date', 'followup_completed')
        }),
        ('Professional Referral', {
            'fields': ('professional_referral_recommended', 'referral_sent', 'referral_type')
        }),
        ('Privacy', {
            'fields': ('student_consented', 'anonymous')
        }),
        ('Timestamp', {
            'fields': ('assessed_at',)
        }),
    )
    
    actions = ['mark_followup_complete', 'send_referrals']
    
    def assessment_id_short(self, obj):
        return str(obj.assessment_id)[:8]
    assessment_id_short.short_description = 'ID'
    
    def risk_badge(self, obj):
        colors = {
            'MINIMAL': '#28a745',
            'MILD': '#17a2b8',
            'MODERATE': '#ffc107',
            'SEVERE': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        icons = {
            'MINIMAL': '✓',
            'MILD': '⚠',
            'MODERATE': '⚠⚠',
            'SEVERE': '⚠⚠⚠',
            'CRITICAL': '🚨'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            colors.get(obj.risk_level, '#6c757d'),
            icons.get(obj.risk_level, ''),
            obj.get_risk_level_display()
        )
    risk_badge.short_description = 'Risk Level'
    
    def score_display(self, obj):
        percentage = (obj.score / obj.max_score) * 100 if obj.max_score > 0 else 0
        return f"{obj.score}/{obj.max_score} ({percentage:.1f}%)"
    score_display.short_description = 'Score'
    
    def responses_display(self, obj):
        return format_html('<pre>{}</pre>', json.dumps(obj.responses, indent=2))
    responses_display.short_description = 'Assessment Responses'
    
    def mark_followup_complete(self, request, queryset):
        updated = queryset.update(followup_completed=True)
        self.message_user(request, f'{updated} follow-up(s) marked as complete.')
    mark_followup_complete.short_description = 'Mark follow-up as complete'
    
    def send_referrals(self, request, queryset):
        updated = queryset.filter(professional_referral_recommended=True).update(referral_sent=True)
        self.message_user(request, f'{updated} referral(s) marked as sent.')
    send_referrals.short_description = 'Mark referrals as sent'


@admin.register(ChatbotKnowledgeBase)
class ChatbotKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['kb_id_short', 'category', 'question_preview', 'is_active', 
                    'priority', 'times_used', 'helpfulness_score']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer', 'keywords']
    readonly_fields = ['kb_id', 'times_used', 'helpful_count', 'not_helpful_count', 
                       'created_at', 'updated_at']
    list_editable = ['is_active', 'priority']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('kb_id', 'category', 'question', 'answer')
        }),
        ('Matching & Search', {
            'fields': ('keywords', 'similar_questions')
        }),
        ('Configuration', {
            'fields': ('is_active', 'priority', 'related_links')
        }),
        ('Statistics', {
            'fields': ('times_used', 'helpful_count', 'not_helpful_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_entries', 'deactivate_entries', 'increase_priority']
    
    def kb_id_short(self, obj):
        return str(obj.kb_id)[:8]
    kb_id_short.short_description = 'ID'
    
    def question_preview(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_preview.short_description = 'Question'
    
    def helpfulness_score(self, obj):
        total = obj.helpful_count + obj.not_helpful_count
        if total == 0:
            return 'N/A'
        percentage = (obj.helpful_count / total) * 100
        color = '#28a745' if percentage >= 70 else '#ffc107' if percentage >= 50 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            percentage
        )
    helpfulness_score.short_description = 'Helpful %'
    
    def activate_entries(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} entry(ies) activated.')
    activate_entries.short_description = 'Activate selected entries'
    
    def deactivate_entries(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} entry(ies) deactivated.')
    deactivate_entries.short_description = 'Deactivate selected entries'
    
    def increase_priority(self, request, queryset):
        for entry in queryset:
            entry.priority += 1
            entry.save()
        self.message_user(request, f'{queryset.count()} entry(ies) priority increased.')
    increase_priority.short_description = 'Increase priority by 1'


@admin.register(ChatbotIntent)
class ChatbotIntentAdmin(admin.ModelAdmin):
    list_display = ['intent_name', 'category', 'priority', 'is_active', 
                    'times_detected', 'accuracy_badge', 'requires_authentication']
    list_filter = ['category', 'is_active', 'requires_authentication']
    search_fields = ['intent_name', 'description', 'category']
    readonly_fields = ['times_detected', 'accuracy_score', 'created_at', 'updated_at']
    list_editable = ['is_active', 'priority']
    
    fieldsets = (
        ('Intent Information', {
            'fields': ('intent_name', 'description', 'category')
        }),
        ('Training Data', {
            'fields': ('training_phrases', 'parameters')
        }),
        ('Response Configuration', {
            'fields': ('response_templates', 'action_type', 'requires_authentication')
        }),
        ('Settings', {
            'fields': ('is_active', 'priority')
        }),
        ('Statistics', {
            'fields': ('times_detected', 'accuracy_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def accuracy_badge(self, obj):
        if obj.accuracy_score is None:
            return 'N/A'
        percentage = obj.accuracy_score * 100
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 60 else '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{:.1f}%</span>',
            color,
            percentage
        )
    accuracy_badge.short_description = 'Accuracy'


@admin.register(ChatbotFeedback)
class ChatbotFeedbackAdmin(admin.ModelAdmin):
    list_display = ['feedback_id_short', 'feedback_type', 'rating_stars', 
                    'sentiment', 'responded', 'created_at']
    list_filter = ['feedback_type', 'rating', 'responded', 'sentiment', DateRangeFilter]
    search_fields = ['feedback_id', 'comment', 'conversation__user__username']
    readonly_fields = ['feedback_id', 'created_at', 'responded_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Feedback Info', {
            'fields': ('feedback_id', 'conversation', 'message', 'feedback_type')
        }),
        ('Rating & Sentiment', {
            'fields': ('rating', 'sentiment')
        }),
        ('Detailed Feedback', {
            'fields': ('comment', 'what_worked', 'what_needs_improvement')
        }),
        ('Response', {
            'fields': ('responded', 'response_text', 'responded_by', 'responded_at')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['mark_as_responded']
    
    def feedback_id_short(self, obj):
        return str(obj.feedback_id)[:8]
    feedback_id_short.short_description = 'ID'
    
    def rating_stars(self, obj):
        if obj.rating:
            stars = '⭐' * obj.rating
            color = '#28a745' if obj.rating >= 4 else '#ffc107' if obj.rating >= 3 else '#dc3545'
            return format_html(
                '<span style="color: {}; font-size: 16px;">{}</span>',
                color,
                stars
            )
        return '-'
    rating_stars.short_description = 'Rating'
    
    def mark_as_responded(self, request, queryset):
        updated = queryset.update(
            responded=True,
            responded_by=request.user,
            responded_at=timezone.now()
        )
        self.message_user(request, f'{updated} feedback(s) marked as responded.')
    mark_as_responded.short_description = 'Mark as responded'


@admin.register(CrisisAlert)
class CrisisAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_id_short', 'student', 'crisis_type', 'severity_badge', 
                    'status_badge', 'detected_at', 'authorities_notified', 'handled_by']
    list_filter = ['crisis_type', 'severity', 'status', 'authorities_notified', 
                   'emergency_contact_called', DateRangeFilter]
    search_fields = ['alert_id', 'student__registration_number', 'student__user__username']
    readonly_fields = ['alert_id', 'detected_at', 'notification_sent_at', 'resolved_at',
                       'detected_keywords_display', 'confidence']
    date_hierarchy = 'detected_at'
    list_per_page = 50
    
    fieldsets = (
        ('⚠️ CRISIS ALERT', {
            'fields': ('alert_id', 'student', 'conversation', 'message'),
            'classes': ('wide',)
        }),
        ('Crisis Details', {
            'fields': ('crisis_type', 'severity', 'detected_keywords_display', 'confidence')
        }),
        ('Status & Response', {
            'fields': ('status', 'auto_response_sent', 'auto_response_text')
        }),
        ('Notifications', {
            'fields': ('authorities_notified', 'notified_users', 'notification_sent_at',
                      'emergency_contact_called')
        }),
        ('Intervention', {
            'fields': ('intervention_notes', 'handled_by', 'resolved_at')
        }),
        ('Timestamp', {
            'fields': ('detected_at',)
        }),
    )
    
    actions = ['notify_authorities', 'mark_as_resolved', 'mark_as_in_progress']
    
    def alert_id_short(self, obj):
        return str(obj.alert_id)[:8]
    alert_id_short.short_description = 'Alert ID'
    
    def severity_badge(self, obj):
        colors = {
            'LOW': '#17a2b8',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 3px; font-weight: bold; font-size: 13px;">🚨 {}</span>',
            colors.get(obj.severity, '#6c757d'),
            obj.severity
        )
    severity_badge.short_description = 'Severity'
    
    def status_badge(self, obj):
        colors = {
            'DETECTED': '#dc3545',
            'NOTIFIED': '#fd7e14',
            'IN_PROGRESS': '#ffc107',
            'RESOLVED': '#28a745',
            'FALSE_ALARM': '#6c757d'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def detected_keywords_display(self, obj):
        return format_html('<pre>{}</pre>', json.dumps(obj.detected_keywords, indent=2))
    detected_keywords_display.short_description = 'Detected Keywords'
    
    def notify_authorities(self, request, queryset):
        for alert in queryset.filter(authorities_notified=False):
            alert.authorities_notified = True
            alert.notification_sent_at = timezone.now()
            alert.status = 'NOTIFIED'
            alert.save()
        self.message_user(request, f'Authorities notified for {queryset.count()} alert(s).')
    notify_authorities.short_description = '🚨 Notify authorities'
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(
            status='RESOLVED',
            resolved_at=timezone.now(),
            handled_by=request.user
        )
        self.message_user(request, f'{updated} alert(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark as resolved'
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(
            status='IN_PROGRESS',
            handled_by=request.user
        )
        self.message_user(request, f'{updated} alert(s) marked as in progress.')
    mark_as_in_progress.short_description = 'Mark as in progress'


@admin.register(ChatbotAnalytics)
class ChatbotAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_conversations', 'total_messages', 'unique_users',
                    'crisis_detected_count', 'avg_satisfaction_rating', 'escalated_conversations']
    list_filter = [DateRangeFilter]
    search_fields = ['date']
    readonly_fields = ['date', 'total_conversations', 'total_messages', 'unique_users',
                       'academic_conversations', 'mental_health_conversations', 
                       'general_conversations', 'positive_sentiment_count',
                       'neutral_sentiment_count', 'negative_sentiment_count',
                       'crisis_detected_count', 'avg_response_time', 
                       'avg_satisfaction_rating', 'escalated_conversations',
                       'total_tokens_used', 'avg_confidence_score',
                       'created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Date', {
            'fields': ('date',)
        }),
        ('Usage Metrics', {
            'fields': ('total_conversations', 'total_messages', 'unique_users')
        }),
        ('Conversation Types', {
            'fields': ('academic_conversations', 'mental_health_conversations', 
                      'general_conversations'),
            'classes': ('collapse',)
        }),
        ('Sentiment Analysis', {
            'fields': ('positive_sentiment_count', 'neutral_sentiment_count',
                      'negative_sentiment_count', 'crisis_detected_count'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('avg_response_time', 'avg_satisfaction_rating', 
                      'escalated_conversations'),
            'classes': ('collapse',)
        }),
        ('AI Metrics', {
            'fields': ('total_tokens_used', 'avg_confidence_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser




# Note: Replace 'main_application' in the conversation_link method with your actual app name


# ========================
# ADMIN SITE CUSTOMIZATION
# ========================

admin.site.site_header = "UoN Faculty of Business - Admin Panel"
admin.site.site_title = "Business Faculty Admin"
admin.site.index_title = "Welcome to Faculty of Business Management System"