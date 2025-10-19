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
    is_published = models.BooleanField(default=True)
    
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
    

# Add these models to your existing models.py file

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

# ========================
# SECURITY & AUDIT TRAIL
# ========================

class AuditLog(models.Model):
    """Comprehensive audit trail for all system actions"""
    ACTION_TYPES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('EXPORT', 'Data Export'),
        ('IMPORT', 'Data Import'),
        ('BULK_ACTION', 'Bulk Action'),
    )
    
    SEVERITY_LEVELS = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )
    
    # Who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                             related_name='audit_logs')
    user_type = models.CharField(max_length=20, blank=True)
    username = models.CharField(max_length=150)  # Store username in case user is deleted
    
    # What action was performed
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    action_description = models.TextField()
    
    # What was affected (Generic relation to any model)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, 
                                     null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional details
    model_name = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)  # String representation of object
    
    # Changes made
    old_values = models.JSONField(null=True, blank=True)  # Previous state
    new_values = models.JSONField(null=True, blank=True)  # New state
    changes_summary = models.TextField(blank=True)
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)  # GET, POST, PUT, DELETE
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Severity for security monitoring
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='LOW')
    is_suspicious = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.action_type} - {self.timestamp}"


class SecurityEvent(models.Model):
    """Track security-related events and threats"""
    EVENT_TYPES = (
        ('BRUTE_FORCE', 'Brute Force Attack'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('DATA_BREACH_ATTEMPT', 'Data Breach Attempt'),
        ('SQL_INJECTION', 'SQL Injection Attempt'),
        ('XSS_ATTEMPT', 'XSS Attack Attempt'),
        ('CSRF_VIOLATION', 'CSRF Violation'),
        ('RATE_LIMIT_EXCEEDED', 'Rate Limit Exceeded'),
        ('PRIVILEGE_ESCALATION', 'Privilege Escalation Attempt'),
        ('MASS_DATA_EXPORT', 'Mass Data Export'),
        ('UNUSUAL_BEHAVIOR', 'Unusual User Behavior'),
    )
    
    RISK_LEVELS = (
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
        ('CRITICAL', 'Critical Risk'),
    )
    
    STATUS_CHOICES = (
        ('DETECTED', 'Detected'),
        ('INVESTIGATING', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
        ('IGNORED', 'Ignored'),
    )
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DETECTED')
    
    # User involved (if any)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='security_events')
    username = models.CharField(max_length=150, blank=True)
    
    # Event details
    description = models.TextField()
    details = models.JSONField(null=True, blank=True)
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_data = models.TextField(blank=True)  # Request payload if relevant
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Response actions
    action_taken = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='resolved_security_events')
    
    # Auto-blocking
    auto_blocked = models.BooleanField(default=False)
    block_duration_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'security_events'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['event_type', '-detected_at']),
            models.Index(fields=['risk_level', 'status']),
            models.Index(fields=['ip_address', '-detected_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.risk_level} - {self.detected_at}"


class LoginAttempt(models.Model):
    """Track all login attempts (successful and failed)"""
    username = models.CharField(max_length=150, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='login_attempts')
    
    # Attempt details
    success = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=200, blank=True)
    
    # Request information
    ip_address = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True)
    
    # Location data (if available)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Session tracking
    session_key = models.CharField(max_length=40, blank=True)
    
    class Meta:
        db_table = 'login_attempts'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['success', '-timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.username} - {status} - {self.timestamp}"


class UserSession(models.Model):
    """Track active user sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    
    # Session information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)  # Mobile, Desktop, Tablet
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    
    # Session status
    is_active = models.BooleanField(default=True)
    
    # Location
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.login_time}"


class SystemSettings(models.Model):
    """System-wide settings including maintenance mode"""
    # Maintenance mode
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default="System is currently under maintenance. Please check back later.")
    maintenance_started_at = models.DateTimeField(null=True, blank=True)
    maintenance_started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                                related_name='maintenance_activations')
    
    # Security settings
    max_login_attempts = models.IntegerField(default=5)
    lockout_duration_minutes = models.IntegerField(default=30)
    session_timeout_minutes = models.IntegerField(default=60)
    require_password_change_days = models.IntegerField(default=90)
    
    # Rate limiting
    api_rate_limit_per_minute = models.IntegerField(default=60)
    enable_rate_limiting = models.BooleanField(default=True)
    
    # Audit settings
    enable_audit_logging = models.BooleanField(default=True)
    audit_log_retention_days = models.IntegerField(default=365)
    log_view_actions = models.BooleanField(default=False)  # Log view operations (creates many logs)
    
    # Security features
    enable_two_factor_auth = models.BooleanField(default=False)
    enable_ip_whitelist = models.BooleanField(default=False)
    whitelist_ips = models.TextField(blank=True, help_text="Comma-separated IP addresses")
    
    # Notifications
    security_alert_emails = models.TextField(blank=True, help_text="Comma-separated email addresses for security alerts")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='settings_updates')
    
    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return f"System Settings (Updated: {self.updated_at})"
    
    def save(self, *args, **kwargs):
        # Ensure only one settings record exists
        if not self.pk and SystemSettings.objects.exists():
            raise ValueError('SystemSettings instance already exists')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create system settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class BlockedIP(models.Model):
    """Track blocked IP addresses"""
    BLOCK_REASONS = (
        ('BRUTE_FORCE', 'Brute Force Attack'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('MANUAL_BLOCK', 'Manual Block'),
        ('AUTOMATED_BLOCK', 'Automated Block'),
    )
    
    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    reason = models.CharField(max_length=30, choices=BLOCK_REASONS)
    description = models.TextField(blank=True)
    
    # Block details
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='blocked_ips')
    blocked_until = models.DateTimeField(null=True, blank=True)  # Null = permanent
    
    # Status
    is_active = models.BooleanField(default=True)
    unblocked_at = models.DateTimeField(null=True, blank=True)
    unblocked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='unblocked_ips')
    
    # Statistics
    block_count = models.IntegerField(default=1)  # How many times this IP has been blocked
    
    class Meta:
        db_table = 'blocked_ips'
        ordering = ['-blocked_at']
        indexes = [
            models.Index(fields=['ip_address', 'is_active']),
            models.Index(fields=['-blocked_at']),
        ]
    
    def __str__(self):
        return f"{self.ip_address} - {self.reason}"
    
    def is_blocked(self):
        """Check if IP is currently blocked"""
        if not self.is_active:
            return False
        if self.blocked_until is None:
            return True
        return timezone.now() < self.blocked_until


class DataExportLog(models.Model):
    """Track data exports for compliance and security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_exports')
    
    # Export details
    export_type = models.CharField(max_length=100)  # Students, Marks, Financial, etc.
    model_name = models.CharField(max_length=100)
    record_count = models.IntegerField()
    
    # Export parameters
    filters_applied = models.JSONField(null=True, blank=True)
    fields_exported = models.JSONField(null=True, blank=True)
    
    # File information
    file_format = models.CharField(max_length=20)  # CSV, Excel, PDF
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Request information
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Security
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_exports')
    
    class Meta:
        db_table = 'data_export_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.export_type} - {self.timestamp}"


# Add these models to your existing models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

# ========================
# AI CHATBOT SYSTEM
# ========================

class ChatbotConversation(models.Model):
    """Track individual chatbot conversations"""
    CONVERSATION_TYPES = (
        ('ACADEMIC', 'Academic Support'),
        ('MENTAL_HEALTH', 'Mental Health Support'),
        ('GENERAL', 'General Inquiry'),
        ('REGISTRATION', 'Registration Help'),
        ('FEES', 'Fees Inquiry'),
        ('GRADES', 'Grades Inquiry'),
        ('TIMETABLE', 'Timetable Inquiry'),
        ('CAREER', 'Career Guidance'),
        ('EMERGENCY', 'Emergency/Crisis'),
    )
    
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
        ('ESCALATED', 'Escalated to Human'),
        ('ARCHIVED', 'Archived'),
    )
    
    SENTIMENT_CHOICES = (
        ('POSITIVE', 'Positive'),
        ('NEUTRAL', 'Neutral'),
        ('NEGATIVE', 'Negative'),
        ('CRISIS', 'Crisis - Needs Immediate Attention'),
    )
    
    conversation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_conversations')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, null=True, blank=True, 
                                related_name='chat_conversations')
    
    # Conversation metadata
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES, default='GENERAL')
    title = models.CharField(max_length=200, blank=True)  # Auto-generated from first message
    
    # Status and sentiment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    overall_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='NEUTRAL')
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # AI metrics
    total_messages = models.IntegerField(default=0)
    ai_responses = models.IntegerField(default=0)
    user_messages = models.IntegerField(default=0)
    avg_response_time_seconds = models.FloatField(default=0.0)
    
    # Escalation
    escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='escalated_chats', 
                                     limit_choices_to={'user_type__in': ['DEAN', 'COD', 'ICT_ADMIN']})
    escalation_reason = models.TextField(blank=True)
    
    # Satisfaction
    user_satisfaction = models.IntegerField(null=True, blank=True, 
                                           help_text="1-5 rating")
    user_feedback = models.TextField(blank=True)
    
    # Session info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'chatbot_conversations'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['conversation_type', '-started_at']),
            models.Index(fields=['overall_sentiment', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.conversation_type} - {self.started_at}"
    
    def close_conversation(self):
        """Close the conversation"""
        self.status = 'CLOSED'
        self.closed_at = timezone.now()
        self.save()
    
    def escalate(self, reason, escalated_to=None):
        """Escalate conversation to human support"""
        self.escalated = True
        self.escalated_at = timezone.now()
        self.escalated_to = escalated_to
        self.escalation_reason = reason
        self.status = 'ESCALATED'
        self.save()


class ChatMessage(models.Model):
    """Individual messages in chatbot conversations"""
    MESSAGE_TYPES = (
        ('USER', 'User Message'),
        ('AI', 'AI Response'),
        ('SYSTEM', 'System Message'),
        ('HUMAN', 'Human Support'),
    )
    
    SENTIMENT_CHOICES = (
        ('POSITIVE', 'Positive'),
        ('NEUTRAL', 'Neutral'),
        ('NEGATIVE', 'Negative'),
        ('ANXIOUS', 'Anxious'),
        ('DEPRESSED', 'Depressed'),
        ('CRISIS', 'Crisis'),
    )
    
    message_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(ChatbotConversation, on_delete=models.CASCADE, 
                                     related_name='messages')
    
    # Message content
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    
    # AI processing
    processed_content = models.TextField(blank=True)  # Cleaned/processed version
    intent_detected = models.CharField(max_length=100, blank=True)  # Academic, Mental Health, etc.
    entities_extracted = models.JSONField(null=True, blank=True)  # Named entities, dates, etc.
    confidence_score = models.FloatField(null=True, blank=True)  # AI confidence (0-1)
    
    # Sentiment analysis
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, default='NEUTRAL')
    sentiment_score = models.FloatField(null=True, blank=True)  # -1 to 1
    emotion_scores = models.JSONField(null=True, blank=True)  # Joy, sadness, anger, etc.
    
    # Crisis detection
    is_crisis = models.BooleanField(default=False)
    crisis_keywords = models.JSONField(null=True, blank=True)
    crisis_level = models.CharField(max_length=20, blank=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Response metadata
    response_time_seconds = models.FloatField(null=True, blank=True)
    model_used = models.CharField(max_length=100, blank=True)  # GPT-4, Custom Model, etc.
    tokens_used = models.IntegerField(null=True, blank=True)
    
    # Attachments
    has_attachment = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='chatbot_attachments/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Feedback
    was_helpful = models.BooleanField(null=True, blank=True)
    feedback_text = models.TextField(blank=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['message_type', 'created_at']),
            models.Index(fields=['is_crisis', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.conversation.user.username} - {self.message_type} - {self.created_at}"


class MentalHealthAssessment(models.Model):
    """Track mental health assessments from chatbot interactions"""
    ASSESSMENT_TYPES = (
        ('PHQ9', 'PHQ-9 (Depression)'),
        ('GAD7', 'GAD-7 (Anxiety)'),
        ('STRESS', 'Stress Assessment'),
        ('WELLBEING', 'General Wellbeing'),
        ('CRISIS', 'Crisis Assessment'),
    )
    
    RISK_LEVELS = (
        ('MINIMAL', 'Minimal Risk'),
        ('MILD', 'Mild Risk'),
        ('MODERATE', 'Moderate Risk'),
        ('SEVERE', 'Severe Risk'),
        ('CRITICAL', 'Critical - Immediate Intervention'),
    )
    
    assessment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, 
                                related_name='mental_health_assessments')
    conversation = models.ForeignKey(ChatbotConversation, on_delete=models.CASCADE, 
                                     related_name='assessments', null=True, blank=True)
    
    # Assessment details
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    score = models.IntegerField()
    max_score = models.IntegerField()
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    
    # Detailed results
    responses = models.JSONField()  # Store all question-answer pairs
    interpretation = models.TextField()
    recommendations = models.TextField()
    
    # Follow-up
    requires_followup = models.BooleanField(default=False)
    followup_date = models.DateField(null=True, blank=True)
    followup_completed = models.BooleanField(default=False)
    
    # Professional referral
    professional_referral_recommended = models.BooleanField(default=False)
    referral_sent = models.BooleanField(default=False)
    referral_type = models.CharField(max_length=100, blank=True)  # Counselor, Psychiatrist, etc.
    
    # Timestamps
    assessed_at = models.DateTimeField(auto_now_add=True)
    
    # Consent and privacy
    student_consented = models.BooleanField(default=True)
    anonymous = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'mental_health_assessments'
        ordering = ['-assessed_at']
        indexes = [
            models.Index(fields=['student', '-assessed_at']),
            models.Index(fields=['risk_level', '-assessed_at']),
            models.Index(fields=['requires_followup', 'followup_completed']),
        ]
    
    def __str__(self):
        return f"{self.student.registration_number} - {self.assessment_type} - {self.risk_level}"


class ChatbotKnowledgeBase(models.Model):
    """Knowledge base for chatbot responses"""
    CATEGORY_CHOICES = (
        ('ACADEMIC', 'Academic'),
        ('MENTAL_HEALTH', 'Mental Health'),
        ('REGISTRATION', 'Registration'),
        ('FEES', 'Fees'),
        ('TIMETABLE', 'Timetable'),
        ('GENERAL', 'General'),
        ('FAQ', 'FAQ'),
        ('POLICY', 'Policy'),
        ('SUPPORT', 'Support Services'),
    )
    
    kb_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Content
    question = models.TextField()
    answer = models.TextField()
    keywords = models.JSONField(default=list)  # For matching
    
    # Alternative phrasings
    similar_questions = models.JSONField(default=list)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)  # Higher priority = shown first
    
    # Usage statistics
    times_used = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Version control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   related_name='created_kb_entries')
    
    # Links to resources
    related_links = models.JSONField(default=list)
    
    class Meta:
        db_table = 'chatbot_knowledge_base'
        ordering = ['-priority', 'category']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-priority']),
        ]
    
    def __str__(self):
        return f"{self.category} - {self.question[:50]}"


class ChatbotIntent(models.Model):
    """Machine learning training data for intent classification"""
    intent_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50)
    
    # Training examples
    training_phrases = models.JSONField(default=list)  # List of example phrases
    
    # Response templates
    response_templates = models.JSONField(default=list)
    
    # Parameters to extract
    parameters = models.JSONField(default=list)  # Entities to extract
    
    # Actions to trigger
    action_type = models.CharField(max_length=100, blank=True)  # Function to call
    requires_authentication = models.BooleanField(default=False)
    
    # Priority
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Statistics
    times_detected = models.IntegerField(default=0)
    accuracy_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_intents'
        ordering = ['-priority', 'intent_name']
    
    def __str__(self):
        return f"{self.intent_name} - {self.category}"


class ChatbotFeedback(models.Model):
    """User feedback on chatbot interactions"""
    FEEDBACK_TYPES = (
        ('RATING', 'Rating'),
        ('BUG', 'Bug Report'),
        ('SUGGESTION', 'Suggestion'),
        ('COMPLAINT', 'Complaint'),
        ('PRAISE', 'Praise'),
    )
    
    feedback_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    conversation = models.ForeignKey(ChatbotConversation, on_delete=models.CASCADE, 
                                     related_name='feedback')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='feedback')
    
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    rating = models.IntegerField(null=True, blank=True)  # 1-5
    
    # Detailed feedback
    comment = models.TextField(blank=True)
    what_worked = models.TextField(blank=True)
    what_needs_improvement = models.TextField(blank=True)
    
    # Sentiment
    sentiment = models.CharField(max_length=20, blank=True)
    
    # Response
    responded = models.BooleanField(default=False)
    response_text = models.TextField(blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='chatbot_feedback_responses')
    responded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chatbot_feedback'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback - {self.feedback_type} - {self.created_at}"


class CrisisAlert(models.Model):
    """Track crisis situations detected by chatbot"""
    CRISIS_TYPES = (
        ('SUICIDE', 'Suicidal Thoughts'),
        ('SELF_HARM', 'Self Harm'),
        ('SEVERE_DEPRESSION', 'Severe Depression'),
        ('PANIC', 'Panic Attack'),
        ('ABUSE', 'Abuse'),
        ('VIOLENCE', 'Violence'),
        ('EMERGENCY', 'Medical Emergency'),
    )
    
    STATUS_CHOICES = (
        ('DETECTED', 'Detected'),
        ('NOTIFIED', 'Authorities Notified'),
        ('IN_PROGRESS', 'Intervention in Progress'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_ALARM', 'False Alarm'),
    )
    
    alert_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, 
                                related_name='crisis_alerts')
    conversation = models.ForeignKey(ChatbotConversation, on_delete=models.CASCADE,
                                     related_name='crisis_alerts')
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE,
                                related_name='crisis_alerts')
    
    # Crisis details
    crisis_type = models.CharField(max_length=20, choices=CRISIS_TYPES)
    severity = models.CharField(max_length=20)  # LOW, MEDIUM, HIGH, CRITICAL
    detected_keywords = models.JSONField()
    confidence = models.FloatField()  # AI confidence in crisis detection
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DETECTED')
    
    # Response
    auto_response_sent = models.BooleanField(default=False)
    auto_response_text = models.TextField(blank=True)
    
    # Notification
    authorities_notified = models.BooleanField(default=False)
    notified_users = models.ManyToManyField(User, related_name='received_crisis_alerts', blank=True)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Follow-up
    intervention_notes = models.TextField(blank=True)
    handled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='handled_crisis_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    
    # Emergency contacts
    emergency_contact_called = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'crisis_alerts'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['student', '-detected_at']),
            models.Index(fields=['status', '-detected_at']),
            models.Index(fields=['severity', 'status']),
        ]
    
    def __str__(self):
        return f"CRISIS: {self.student.registration_number} - {self.crisis_type} - {self.severity}"


class ChatbotAnalytics(models.Model):
    """Daily analytics for chatbot usage"""
    date = models.DateField(unique=True, db_index=True)
    
    # Usage metrics
    total_conversations = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    
    # Conversation types
    academic_conversations = models.IntegerField(default=0)
    mental_health_conversations = models.IntegerField(default=0)
    general_conversations = models.IntegerField(default=0)
    
    # Sentiment
    positive_sentiment_count = models.IntegerField(default=0)
    neutral_sentiment_count = models.IntegerField(default=0)
    negative_sentiment_count = models.IntegerField(default=0)
    crisis_detected_count = models.IntegerField(default=0)
    
    # Performance
    avg_response_time = models.FloatField(default=0.0)
    avg_satisfaction_rating = models.FloatField(null=True, blank=True)
    
    # Escalations
    escalated_conversations = models.IntegerField(default=0)
    
    # AI metrics
    total_tokens_used = models.IntegerField(default=0)
    avg_confidence_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_analytics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics - {self.date}"