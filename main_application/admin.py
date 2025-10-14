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
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active_user', 'is_staff')
    list_filter = ('user_type', 'is_active_user', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('username',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'is_active_user')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('user_type', 'phone_number', 'profile_picture', 'is_active_user')
        }),
    )


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


# ========================
# ADMIN SITE CUSTOMIZATION
# ========================

admin.site.site_header = "UoN Faculty of Business - Admin Panel"
admin.site.site_title = "Business Faculty Admin"
admin.site.index_title = "Welcome to Faculty of Business Management System"