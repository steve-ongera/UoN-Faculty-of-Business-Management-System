from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# ========================
# CORE USER MANAGEMENT
# ========================

class User(AbstractUser):
    """Extended user model for all system users"""
    USER_TYPES = (
        ('STUDENT', 'Student'),
        ('LECTURER', 'Lecturer'),
        ('COD', 'Chairman of Department'),
        ('DEAN', 'Dean'),
        ('ICT_ADMIN', 'ICT Administrator'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active_user = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type})"


# ========================
# ACADEMIC STRUCTURE
# ========================

class AcademicYear(models.Model):
    """Academic years like 2024/2025, 2025/2026"""
    year_code = models.CharField(max_length=20, unique=True)  # e.g., "2024/2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.year_code


class Semester(models.Model):
    """Semesters within academic years"""
    SEMESTER_CHOICES = (
        (1, 'Semester 1'),
        (2, 'Semester 2'),
        (3, 'Semester 3'),
    )
    
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.IntegerField(choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    registration_deadline = models.DateField()
    
    class Meta:
        db_table = 'semesters'
        unique_together = ('academic_year', 'semester_number')
        ordering = ['-academic_year', 'semester_number']
    
    def __str__(self):
        return f"{self.academic_year.year_code} - Semester {self.semester_number}"


class Intake(models.Model):
    """Different intakes for student admission"""
    INTAKE_TYPES = (
        ('SEPTEMBER', 'September Intake'),
        ('JANUARY', 'January Intake'),
        ('MAY', 'May Intake'),
    )
    
    name = models.CharField(max_length=50)
    intake_type = models.CharField(max_length=20, choices=INTAKE_TYPES)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='intakes')
    intake_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'intakes'
        ordering = ['-intake_date']
    
    def __str__(self):
        return f"{self.name} - {self.academic_year.year_code}"


class Department(models.Model):
    """Departments within the Faculty of Business"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                           related_name='headed_departments', limit_choices_to={'user_type': 'COD'})
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'departments'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Programme(models.Model):
    """Academic programmes offered by the Faculty"""
    PROGRAMME_LEVELS = (
        ('CERTIFICATE', 'Certificate'),
        ('DIPLOMA', 'Diploma'),
        ('BACHELORS', 'Bachelor\'s Degree'),
        ('MASTERS', 'Master\'s Degree'),
        ('PHD', 'Doctor of Philosophy'),
    )
    
    DURATION_YEARS = (
        (1, '1 Year'),
        (2, '2 Years'),
        (3, '3 Years'),
        (4, '4 Years'),
        (5, '5 Years'),
    )
    
    SEMESTERS_PER_YEAR = (
        (2, '2 Semesters'),
        (3, '3 Semesters'),
    )
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    level = models.CharField(max_length=20, choices=PROGRAMME_LEVELS)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programmes')
    duration_years = models.IntegerField(choices=DURATION_YEARS)
    semesters_per_year = models.IntegerField(choices=SEMESTERS_PER_YEAR, default=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'programmes'
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Unit(models.Model):
    """Academic units/courses"""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credit_hours = models.IntegerField(default=3)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='units')
    is_core = models.BooleanField(default=True)  # Core or Elective
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='required_for')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'units'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class ProgrammeUnit(models.Model):
    """Units offered in specific programmes and year levels"""
    YEAR_LEVELS = (
        (1, 'Year 1'),
        (2, 'Year 2'),
        (3, 'Year 3'),
        (4, 'Year 4'),
    )
    
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='programme_units')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='offered_in_programmes')
    year_level = models.IntegerField(choices=YEAR_LEVELS)
    semester = models.IntegerField(choices=Semester.SEMESTER_CHOICES)
    is_mandatory = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'programme_units'
        unique_together = ('programme', 'unit', 'year_level', 'semester')
        ordering = ['programme', 'year_level', 'semester']
    
    def __str__(self):
        return f"{self.programme.code} - {self.unit.code} (Year {self.year_level}, Sem {self.semester})"


# ========================
# STUDENT MANAGEMENT
# ========================

class Student(models.Model):
    """Student profile extending User model"""
    YEAR_LEVELS = (
        (1, 'Year 1'),
        (2, 'Year 2'),
        (3, 'Year 3'),
        (4, 'Year 4'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    registration_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30, blank=True)
    programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name='students')
    current_year = models.IntegerField(choices=YEAR_LEVELS)
    intake = models.ForeignKey(Intake, on_delete=models.PROTECT, related_name='students')
    admission_date = models.DateField()
    is_active = models.BooleanField(default=True)
    can_upgrade = models.BooleanField(default=False)  # For progression to next level

    # --- Additional Personal Details ---
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    # --- Parent Details ---
    parent_name = models.CharField(max_length=100, blank=True, null=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)

    # --- Guardian Details ---
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_phone = models.CharField(max_length=15, blank=True, null=True)
    
    class Meta:
        db_table = 'students'
        ordering = ['registration_number']
    
    def __str__(self):
        return f"{self.registration_number} - {self.user.get_full_name()}"


class StudentProgression(models.Model):
    """Track student progression through different levels"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='progressions')
    from_programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name='graduated_students')
    to_programme = models.ForeignKey(Programme, on_delete=models.PROTECT, related_name='upgraded_students', 
                                     null=True, blank=True)
    completion_date = models.DateField()
    upgrade_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'student_progressions'
        ordering = ['-completion_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.from_programme.code} to {self.to_programme.code if self.to_programme else 'Graduated'}"


class UnitEnrollment(models.Model):
    """Student enrollment in units"""
    ENROLLMENT_STATUS = (
        ('ENROLLED', 'Enrolled'),
        ('DROPPED', 'Dropped'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='enrollments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='ENROLLED')
    
    class Meta:
        db_table = 'unit_enrollments'
        unique_together = ('student', 'unit', 'semester')
        ordering = ['-enrollment_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.unit.code} ({self.semester})"


class SemesterRegistration(models.Model):
    """Student registration for semesters"""
    REGISTRATION_STATUS = (
        ('REGISTERED', 'Registered'),
        ('DEFERRED', 'Deferred'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='semester_registrations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REGISTRATION_STATUS, default='REGISTERED')
    units_enrolled = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'semester_registrations'
        unique_together = ('student', 'semester')
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.semester}"


# ========================
# LECTURER MANAGEMENT
# ========================

class Lecturer(models.Model):
    """Lecturer profile extending User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='lecturer_profile')
    staff_number = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='lecturers')
    specialization = models.CharField(max_length=200, blank=True)
    office_location = models.CharField(max_length=100, blank=True)
    consultation_hours = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'lecturers'
        ordering = ['staff_number']
    
    def __str__(self):
        return f"{self.staff_number} - {self.user.get_full_name()}"


class UnitAllocation(models.Model):
    """Allocation of units to lecturers"""
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='allocations')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='unit_allocations')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='unit_allocations')
    programmes = models.ManyToManyField(Programme, related_name='unit_allocations')  # Which programmes this allocation covers
    is_active = models.BooleanField(default=True)
    allocated_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'unit_allocations'
        unique_together = ('unit', 'lecturer', 'semester')
        ordering = ['-allocated_date']
    
    def __str__(self):
        return f"{self.lecturer.staff_number} - {self.unit.code} ({self.semester})"


# ========================
# GRADING & ASSESSMENT
# ========================

class GradingScheme(models.Model):
    """Grading schemes for different programmes"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='grading_schemes')
    grade = models.CharField(max_length=5)  # A, B, C,  D , F etc.
    min_marks = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    description = models.CharField(max_length=50)  # Pass, Fail, Distinction, etc.
    
    class Meta:
        db_table = 'grading_schemes'
        ordering = ['programme', '-min_marks']
        unique_together = ('programme', 'grade')
    
    def __str__(self):
        return f"{self.programme.code} - {self.grade} ({self.min_marks}-{self.max_marks})"


class AssessmentComponent(models.Model):
    """Assessment components like CATs, Assignments, Exams"""
    COMPONENT_TYPES = (
        ('CAT', 'Continuous Assessment Test'),
        ('ASSIGNMENT', 'Assignment'),
        ('PROJECT', 'Project'),
        ('EXAM', 'Final Examination'),
        ('PRACTICAL', 'Practical'),
    )
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='assessment_components')
    name = models.CharField(max_length=100)
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    
    class Meta:
        db_table = 'assessment_components'
        ordering = ['unit', 'component_type']
    
    def __str__(self):
        return f"{self.unit.code} - {self.name} ({self.weight_percentage}%)"


class StudentMarks(models.Model):
    """Student marks for assessment components"""
    enrollment = models.ForeignKey(UnitEnrollment, on_delete=models.CASCADE, related_name='marks')
    assessment_component = models.ForeignKey(AssessmentComponent, on_delete=models.CASCADE, related_name='student_marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                         validators=[MinValueValidator(0)])
    entered_by = models.ForeignKey(Lecturer, on_delete=models.PROTECT, related_name='entered_marks')
    entry_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        db_table = 'student_marks'
        unique_together = ('enrollment', 'assessment_component')
        ordering = ['-entry_date']
    
    def __str__(self):
        return f"{self.enrollment.student.registration_number} - {self.assessment_component.name}: {self.marks_obtained}"


class FinalGrade(models.Model):
    """Final grades for students in units"""
    enrollment = models.OneToOneField(UnitEnrollment, on_delete=models.CASCADE, related_name='final_grade')
    total_marks = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=5)
    grade_point = models.DecimalField(max_digits=3, decimal_places=2)
    computed_date = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(Lecturer, on_delete=models.PROTECT, related_name='approved_grades', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'final_grades'
        ordering = ['-computed_date']
    
    def __str__(self):
        return f"{self.enrollment.student.registration_number} - {self.enrollment.unit.code}: {self.grade}"


# ========================
# TIMETABLING
# ========================

class Venue(models.Model):
    """Class venues/rooms"""
    VENUE_TYPES = (
        ('LECTURE_HALL', 'Lecture Hall'),
        ('TUTORIAL_ROOM', 'Tutorial Room'),
        ('LAB', 'Laboratory'),
        ('SEMINAR_ROOM', 'Seminar Room'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPES)
    capacity = models.IntegerField()
    building = models.CharField(max_length=100)
    floor = models.CharField(max_length=20, blank=True)
    has_projector = models.BooleanField(default=False)
    has_computers = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'venues'
        ordering = ['building', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name} (Capacity: {self.capacity})"


class TimetableSlot(models.Model):
    """Individual timetable entries"""
    DAYS_OF_WEEK = (
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
    )
    
    unit_allocation = models.ForeignKey(UnitAllocation, on_delete=models.CASCADE, related_name='timetable_slots')
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name='timetable_slots')
    day_of_week = models.CharField(max_length=20, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='timetable_slots')
    year_level = models.IntegerField(choices=Student.YEAR_LEVELS)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_timetables')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'timetable_slots'
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.unit_allocation.unit.code} - {self.day_of_week} {self.start_time}-{self.end_time} @ {self.venue.code}"


# ========================
# FEES MANAGEMENT
# ========================

class FeeStructure(models.Model):
    """Fee structure for programmes"""
    programme = models.ForeignKey(Programme, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_structures')
    year_level = models.IntegerField(choices=Student.YEAR_LEVELS)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    examination_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'fee_structures'
        unique_together = ('programme', 'academic_year', 'year_level')
        ordering = ['programme', 'year_level']
    
    def __str__(self):
        return f"{self.programme.code} - Year {self.year_level} ({self.academic_year.year_code}): KES {self.total_fee}"


class FeePayment(models.Model):
    """Student fee payments"""
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('PARTIAL', 'Partially Paid'),
        ('COMPLETE', 'Fully Paid'),
        ('OVERPAID', 'Overpaid'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    receipt_number = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=50)  # M-Pesa, Bank, Cash, etc.
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'fee_payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.receipt_number}: KES {self.amount_paid}"


class FeeStatement(models.Model):
    """Student fee statement summary"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_statements')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='fee_statements')
    total_billed = models.DecimalField(max_digits=10, decimal_places=2)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    can_register = models.BooleanField(default=True)  # If balance allows registration
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fee_statements'
        unique_together = ('student', 'semester')
        ordering = ['-semester']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.semester}: Balance KES {self.balance}"


# ========================
# COMMUNICATION
# ========================

class Announcement(models.Model):
    """Faculty-wide or targeted announcements"""
    PRIORITY_LEVELS = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_announcements')
    target_programmes = models.ManyToManyField(Programme, blank=True, related_name='announcements')
    target_year_levels = models.CharField(max_length=50, blank=True)  # Comma-separated: "1,2,3"
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='NORMAL')
    publish_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    attachments = models.FileField(upload_to='announcements/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'announcements'
        ordering = ['-publish_date']
    
    def __str__(self):
        return f"{self.title} ({self.priority})"


class Event(models.Model):
    """Faculty events"""
    EVENT_TYPES = (
        ('SEMINAR', 'Seminar'),
        ('WORKSHOP', 'Workshop'),
        ('CONFERENCE', 'Conference'),
        ('MEETING', 'Meeting'),
        ('ORIENTATION', 'Orientation'),
        ('EXAMINATION', 'Examination'),
        ('OTHER', 'Other'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    organizer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='organized_events')
    target_programmes = models.ManyToManyField(Programme, blank=True, related_name='events')
    is_mandatory = models.BooleanField(default=False)
    registration_required = models.BooleanField(default=False)
    max_attendees = models.IntegerField(null=True, blank=True)
    poster = models.ImageField(upload_to='events/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'events'
        ordering = ['-event_date', '-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.event_date}"


class EventRegistration(models.Model):
    """Student registration for events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='event_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'event_registrations'
        unique_together = ('event', 'student')
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.event.title}"


class Message(models.Model):
    """Direct messaging between users"""
    MESSAGE_TYPES = (
        ('DIRECT', 'Direct Message'),
        ('BROADCAST', 'Broadcast'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipients = models.ManyToManyField(User, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='DIRECT')
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    attachments = models.FileField(upload_to='messages/', blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"From {self.sender.username}: {self.subject}"


class MessageReadStatus(models.Model):
    """Track read status of messages"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_read_statuses')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'message_read_statuses'
        unique_together = ('message', 'recipient')
    
    def __str__(self):
        return