"""
Django management command to seed the database with realistic Kenyan data
for University of Nairobi - Faculty of Business
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

from main_application.models import (
    User, AcademicYear, Semester, Intake, Department, Programme, Unit,
    ProgrammeUnit, Student, Lecturer, UnitAllocation, GradingScheme,
    AssessmentComponent, Venue, FeeStructure, Announcement, Event
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with realistic UoN Faculty of Business data'

    # Kenyan names by tribe
    KENYAN_NAMES = {
        'Kikuyu': {
            'first': ['Kamau', 'Njoroge', 'Wanjiru', 'Kariuki', 'Muthoni', 'Nyambura', 
                     'Gitau', 'Kinyua', 'Muchiri', 'Gichuki', 'Ngina', 'Waruguru'],
            'last': ['Kamau', 'Njoroge', 'Kariuki', 'Muthee', 'Gitau', 'Kinyua', 
                    'Mwangi', 'Ochienga', 'Kipchoge', 'Mutua', 'Nyambura', 'Kiplagat']
        },
        'Luhya': {
            'first': ['Wekesa', 'Ochieng', 'Makokha', 'Mudavadi', 'Nasimiya', 'Khavere',
                     'Mutua', 'Kipchoge', 'Omondi', 'Achieng', 'Juma', 'Miruka'],
            'last': ['Wekesa', 'Makokha', 'Mudavadi', 'Khavere', 'Kipchoge', 'Achieng',
                    'Mutua', 'Omondi', 'Miruka', 'Ochieng', 'Juma', 'Kiplagat']
        },
        'Luo': {
            'first': ['Ochieng', 'Kipchoge', 'Omondi', 'Achieng', 'Kiplagat', 'Odinga',
                     'Oketch', 'Otieno', 'Kipkemboi', 'Kipkoskei', 'Kiplagat', 'Kipchoge'],
            'last': ['Ochieng', 'Kipchoge', 'Kiplagat', 'Odinga', 'Oketch', 'Otieno',
                    'Kipkemboi', 'Kipkoskei', 'Kiplagat', 'Kipchoge', 'Kipkemboi', 'Kiplagat']
        },
        'Kalenjin': {
            'first': ['Kiplagat', 'Kipchoge', 'Kipkemboi', 'Kipkoskei', 'Kiplagat', 'Kipchoge',
                     'Kipkemboi', 'Kipkoskei', 'Kiplagat', 'Kipchoge', 'Kipkemboi', 'Kipkoskei'],
            'last': ['Kiplagat', 'Kipchoge', 'Kipkemboi', 'Kipkoskei', 'Kiplagat', 'Kipchoge',
                    'Kipkemboi', 'Kipkoskei', 'Kiplagat', 'Kipchoge', 'Kipkemboi', 'Kipkoskei']
        },
        'Kikuyu2': {
            'first': ['Muiruri', 'Mwangi', 'Gitau', 'Kinyua', 'Muchiri', 'Gichuki',
                     'Wambui', 'Wairimu', 'Gathoni', 'Macharia', 'Njuguna', 'Mwangi'],
            'last': ['Muiruri', 'Mwangi', 'Gitau', 'Kinyua', 'Muchiri', 'Gichuki',
                    'Wambui', 'Wairimu', 'Gathoni', 'Macharia', 'Njuguna', 'Mwangi']
        },
        'Samburu': {
            'first': ['Lekutuk', 'Lemurian', 'Lemayian', 'Lesanyan', 'Lepata', 'Lemusyon',
                     'Lengitae', 'Lelipet', 'Lesamis', 'Lekukuya', 'Lemasusai', 'Lemayan'],
            'last': ['Lekutuk', 'Lemurian', 'Lemayian', 'Lesanyan', 'Lepata', 'Lemuyon',
                    'Lengitae', 'Lelipet', 'Lesamis', 'Lekukuya', 'Lemasusai', 'Lemayan']
        },
        'Maasai': {
            'first': ['Kipchoge', 'Lesuuda', 'Kipchoge', 'Kipkemboi', 'Lemurian', 'Lemayian',
                     'Lesanyan', 'Lepata', 'Lemuyon', 'Lengitae', 'Lelipet', 'Lesamis'],
            'last': ['Kipchoge', 'Lesuuda', 'Kipchoge', 'Kipkemboi', 'Lemurian', 'Lemayian',
                    'Lesanyan', 'Lepata', 'Lemuyon', 'Lengitae', 'Lelipet', 'Lesamis']
        },
        'Somali': {
            'first': ['Ali', 'Hassan', 'Mohamed', 'Ibrahim', 'Omar', 'Fatima', 'Amina',
                     'Maryam', 'Zainab', 'Layla', 'Hana', 'Asha'],
            'last': ['Ahmed', 'Hassan', 'Mohamed', 'Ibrahim', 'Omar', 'Abdullah', 'Farah',
                    'Abdi', 'Dahir', 'Yusuf', 'Kadir', 'Yussuf']
        },
        'Swahili': {
            'first': ['Rashid', 'Salim', 'Khalid', 'Fatima', 'Zainab', 'Amina', 'Layla',
                     'Hana', 'Asha', 'Jamila', 'Nadia', 'Yasmin'],
            'last': ['Khaled', 'Salim', 'Rashid', 'Hassan', 'Ali', 'Abdullah', 'Farah',
                    'Ahmed', 'Mohamed', 'Ibrahim', 'Omar', 'Yusuf']
        },
        'Kamba': {
            'first': ['Mutua', 'Mule', 'Muli', 'Musyoka', 'Mwathi', 'Kyalo', 'Kalu',
                     'Wambui', 'Wangechi', 'Mwalimu', 'Mzalendo', 'Mwamba'],
            'last': ['Mutua', 'Mule', 'Muli', 'Musyoka', 'Mwathi', 'Kyalo', 'Kalu',
                    'Wambui', 'Wangechi', 'Mwalimu', 'Mzalendo', 'Mwamba']
        },
        'Meru': {
            'first': ['Gitau', 'Kinyua', 'Muchiri', 'Gichuki', 'Wambui', 'Wairimu', 'Gathoni',
                     'Macharia', 'Njuguna', 'Mwangi', 'Muiruri', 'Gitari'],
            'last': ['Gitau', 'Kinyua', 'Muchiri', 'Gichuki', 'Wambui', 'Wairimu', 'Gathoni',
                    'Macharia', 'Njuguna', 'Mwangi', 'Muiruri', 'Gitari']
        },
    }

    RELIGIONS = ['Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 'Other']

    DEPARTMENTS = [
        {'code': 'ACC', 'name': 'Department of Accounting'},
        {'code': 'FIN', 'name': 'Department of Finance'},
        {'code': 'MGT', 'name': 'Department of Management'},
        {'code': 'ECO', 'name': 'Department of Economics'},
        {'code': 'MKT', 'name': 'Department of Marketing'},
    ]

    PROGRAMMES = [
        {'code': 'SC', 'name': 'Bachelor of Science in Business', 'level': 'Undergraduate', 'dept': 'ACC', 'duration': 4},
        {'code': 'BA', 'name': 'Bachelor of Arts in Business', 'level': 'Undergraduate', 'dept': 'MGT', 'duration': 3},
        {'code': 'BCA', 'name': 'Bachelor of Commerce', 'level': 'Undergraduate', 'dept': 'ACC', 'duration': 3},
        {'code': 'MBA', 'name': 'Master of Business Administration', 'level': 'Postgraduate', 'dept': 'MGT', 'duration': 2},
    ]

    UNITS = [
        {'code': 'BUS101', 'name': 'Introduction to Business', 'credit_hours': 3, 'dept': 'MGT', 'core': True},
        {'code': 'ACC101', 'name': 'Financial Accounting I', 'credit_hours': 4, 'dept': 'ACC', 'core': True},
        {'code': 'ECO101', 'name': 'Principles of Economics', 'credit_hours': 3, 'dept': 'ECO', 'core': True},
        {'code': 'MKT101', 'name': 'Marketing Management', 'credit_hours': 3, 'dept': 'MKT', 'core': False},
        {'code': 'FIN101', 'name': 'Introduction to Finance', 'credit_hours': 3, 'dept': 'FIN', 'core': True},
        {'code': 'ACC102', 'name': 'Financial Accounting II', 'credit_hours': 4, 'dept': 'ACC', 'core': True},
        {'code': 'BUS201', 'name': 'Strategic Management', 'credit_hours': 3, 'dept': 'MGT', 'core': True},
        {'code': 'MKT201', 'name': 'Consumer Behavior', 'credit_hours': 3, 'dept': 'MKT', 'core': False},
        {'code': 'FIN201', 'name': 'Corporate Finance', 'credit_hours': 4, 'dept': 'FIN', 'core': True},
        {'code': 'ECO201', 'name': 'Macroeconomics', 'credit_hours': 3, 'dept': 'ECO', 'core': True},
    ]

    LECTURERS = [
        {'name': 'Dr. James Kariuki', 'spec': 'Accounting', 'dept': 'ACC'},
        {'name': 'Prof. Mary Wanjiru', 'spec': 'Finance', 'dept': 'FIN'},
        {'name': 'Dr. Peter Ochieng', 'spec': 'Management', 'dept': 'MGT'},
        {'name': 'Dr. Grace Mutua', 'spec': 'Marketing', 'dept': 'MKT'},
        {'name': 'Prof. David Kiplagat', 'spec': 'Economics', 'dept': 'ECO'},
        {'name': 'Dr. Lucy Muthoni', 'spec': 'Accounting', 'dept': 'ACC'},
        {'name': 'Dr. Samuel Kipchoge', 'spec': 'Finance', 'dept': 'FIN'},
        {'name': 'Dr. Ann Kamau', 'spec': 'Management', 'dept': 'MGT'},
        {'name': 'Dr. Joseph Kipkemboi', 'spec': 'Marketing', 'dept': 'MKT'},
        {'name': 'Prof. Catherine Achieng', 'spec': 'Economics', 'dept': 'ECO'},
    ]

    VENUES = [
        {'code': 'LH01', 'name': 'Lecture Hall 01', 'type': 'Lecture Hall', 'capacity': 100, 'building': 'Business Block A', 'floor': 1},
        {'code': 'LH02', 'name': 'Lecture Hall 02', 'type': 'Lecture Hall', 'capacity': 80, 'building': 'Business Block A', 'floor': 2},
        {'code': 'LH03', 'name': 'Lecture Hall 03', 'type': 'Lecture Hall', 'capacity': 120, 'building': 'Business Block B', 'floor': 1},
        {'code': 'LB01', 'name': 'Lab 01', 'type': 'Laboratory', 'capacity': 40, 'building': 'Business Block B', 'floor': 2},
        {'code': 'LB02', 'name': 'Lab 02', 'type': 'Laboratory', 'capacity': 35, 'building': 'Business Block C', 'floor': 1},
        {'code': 'TR01', 'name': 'Tutorial Room 01', 'type': 'Tutorial Room', 'capacity': 30, 'building': 'Business Block A', 'floor': 3},
        {'code': 'TR02', 'name': 'Tutorial Room 02', 'type': 'Tutorial Room', 'capacity': 25, 'building': 'Business Block C', 'floor': 1},
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        
        try:
            self.create_academic_years()
            self.create_semesters()
            self.create_intakes()
            self.create_departments()
            self.create_programmes()
            self.create_units()
            self.create_programme_units()
            self.create_lecturers()
            self.create_unit_allocations()
            self.create_venues()
            self.create_grading_schemes()
            self.create_assessment_components()
            self.create_students()
            self.create_fee_structures()
            self.create_announcements()
            self.create_events()
            
            self.stdout.write(self.style.SUCCESS('✓ Database seeding completed successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error during seeding: {str(e)}'))

    def create_academic_years(self):
        self.stdout.write('Creating academic years...')
        years = [
            AcademicYear(year_code='2021/2022', start_date=datetime(2021, 9, 1), 
                        end_date=datetime(2022, 8, 31), is_current=False),
            AcademicYear(year_code='2022/2023', start_date=datetime(2022, 9, 1), 
                        end_date=datetime(2023, 8, 31), is_current=False),
            AcademicYear(year_code='2023/2024', start_date=datetime(2023, 9, 1), 
                        end_date=datetime(2024, 8, 31), is_current=False),
            AcademicYear(year_code='2024/2025', start_date=datetime(2024, 9, 1), 
                        end_date=datetime(2025, 8, 31), is_current=True),
        ]
        AcademicYear.objects.bulk_create(years, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS('  ✓ Academic years created'))

    def create_semesters(self):
        self.stdout.write('Creating semesters...')
        academic_years = AcademicYear.objects.all()
        semesters = []
        
        for year in academic_years:
            semesters.append(
                Semester(
                    academic_year=year,
                    semester_number=1,
                    start_date=year.start_date,
                    end_date=year.start_date + timedelta(days=120),
                    registration_deadline=year.start_date + timedelta(days=7),
                    is_current=(year.is_current and True or False)
                )
            )
            semesters.append(
                Semester(
                    academic_year=year,
                    semester_number=2,
                    start_date=year.start_date + timedelta(days=125),
                    end_date=year.end_date,
                    registration_deadline=year.start_date + timedelta(days=132),
                    is_current=False
                )
            )
        
        Semester.objects.bulk_create(semesters, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS('  ✓ Semesters created'))

    def create_intakes(self):
        self.stdout.write('Creating intakes...')
        intakes = [
            Intake(name='Main Intake', intake_type='Main', academic_year=AcademicYear.objects.filter(is_current=True).first(),
                  intake_date=datetime(2024, 9, 1), is_active=True),
            Intake(name='Second Intake', intake_type='Second', academic_year=AcademicYear.objects.filter(is_current=True).first(),
                  intake_date=datetime(2025, 1, 15), is_active=False),
        ]
        Intake.objects.bulk_create(intakes, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS('  ✓ Intakes created'))

    def create_departments(self):
        self.stdout.write('Creating departments...')
        departments = []
        for dept in self.DEPARTMENTS:
            departments.append(
                Department(code=dept['code'], name=dept['name'], head_of_department=None)
            )
        Department.objects.bulk_create(departments, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(departments)} departments created'))

    def create_programmes(self):
        self.stdout.write('Creating programmes...')
        programmes = []
        for prog in self.PROGRAMMES:
            dept = Department.objects.get(code=prog['dept'])
            programmes.append(
                Programme(
                    code=prog['code'],
                    name=prog['name'],
                    level=prog['level'],
                    department=dept,
                    duration_years=prog['duration'],
                    semesters_per_year=2,
                    is_active=True
                )
            )
        Programme.objects.bulk_create(programmes, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(programmes)} programmes created'))

    def create_units(self):
        self.stdout.write('Creating units...')
        units = []
        for unit in self.UNITS:
            dept = Department.objects.get(code=unit['dept'])
            units.append(
                Unit(
                    code=unit['code'],
                    name=unit['name'],
                    credit_hours=unit['credit_hours'],
                    department=dept,
                    is_core=unit['core']
                )
            )
        Unit.objects.bulk_create(units, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(units)} units created'))

    def create_programme_units(self):
        self.stdout.write('Creating programme units...')
        programme_units = []
        programmes = Programme.objects.all()
        units = Unit.objects.all()
        
        for prog in programmes:
            unit_count = 0
            for year_level in range(1, prog.duration_years + 1):
                for semester in [1, 2]:
                    for unit in units[:5]:
                        if unit_count < len(units):
                            programme_units.append(
                                ProgrammeUnit(
                                    programme=prog,
                                    unit=units[unit_count % len(units)],
                                    year_level=year_level,
                                    semester=semester,
                                    is_mandatory=True
                                )
                            )
                            unit_count += 1
        
        ProgrammeUnit.objects.bulk_create(programme_units, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(programme_units)} programme units created'))

    def create_lecturers(self):
        self.stdout.write('Creating lecturers...')
        lecturers = []
        
        for i, lecturer_info in enumerate(self.LECTURERS):
            user = User.objects.create_user(
                username=f'lec{i+1:03d}',
                email=f'lecturer{i+1}@uonbi.ac.ke',
                password='password123',
                first_name=lecturer_info['name'].split()[0],
                last_name=' '.join(lecturer_info['name'].split()[1:]),
                user_type='Lecturer',
                phone_number=f'+254{random.randint(7,9)}{random.randint(10000000,99999999)}',
                is_active_user=True
            )
            
            dept = Department.objects.get(code=lecturer_info['dept'])
            lecturers.append(
                Lecturer(
                    user=user,
                    staff_number=f"STF{i+1:05d}",
                    department=dept,
                    specialization=lecturer_info['spec'],
                    office_location=f"Office {i+1}, Business Block A",
                    is_active=True
                )
            )
        
        Lecturer.objects.bulk_create(lecturers)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(lecturers)} lecturers created'))

    def create_unit_allocations(self):
        self.stdout.write('Creating unit allocations...')
        current_semester = Semester.objects.filter(is_current=True).first()
        lecturers = Lecturer.objects.all()
        units = Unit.objects.all()
        programmes = Programme.objects.all()
        
        allocations = []
        for unit in units:
            lecturer = random.choice(lecturers)
            alloc = UnitAllocation(
                unit=unit,
                lecturer=lecturer,
                semester=current_semester,
                is_active=True
            )
            alloc.save()
            alloc.programmes.set(programmes)
            allocations.append(alloc)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(allocations)} unit allocations created'))

    def create_venues(self):
        self.stdout.write('Creating venues...')
        venues = []
        for venue in self.VENUES:
            venues.append(
                Venue(
                    code=venue['code'],
                    name=venue['name'],
                    venue_type=venue['type'],
                    capacity=venue['capacity'],
                    building=venue['building'],
                    floor=venue['floor'],
                    has_projector=random.choice([True, False]),
                    has_computers=venue['type'] == 'Laboratory',
                    is_available=True
                )
            )
        Venue.objects.bulk_create(venues, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(venues)} venues created'))

    def create_grading_schemes(self):
        self.stdout.write('Creating grading schemes...')
        programmes = Programme.objects.all()
        grades_data = [
            ('A', 70, 100, 4.0, 'Excellent'),
            ('B+', 60, 69, 3.5, 'Very Good'),
            ('B', 50, 59, 3.0, 'Good'),
            ('B-', 40, 49, 2.5, 'Satisfactory'),
            ('C', 30, 39, 2.0, 'Pass'),
            ('D', 20, 29, 1.0, 'Weak Pass'),
            ('F', 0, 19, 0.0, 'Fail'),
        ]
        
        grading_schemes = []
        for prog in programmes:
            for grade, min_m, max_m, gp, desc in grades_data:
                grading_schemes.append(
                    GradingScheme(
                        programme=prog,
                        grade=grade,
                        min_marks=min_m,
                        max_marks=max_m,
                        grade_point=Decimal(str(gp)),
                        description=desc
                    )
                )
        
        GradingScheme.objects.bulk_create(grading_schemes, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Grading schemes created'))

    def create_assessment_components(self):
        self.stdout.write('Creating assessment components...')
        units = Unit.objects.all()
        components = []
        
        for unit in units:
            components.append(
                AssessmentComponent(
                    unit=unit,
                    name='Continuous Assessment',
                    component_type='CA',
                    weight_percentage=40,
                    max_marks=40
                )
            )
            components.append(
                AssessmentComponent(
                    unit=unit,
                    name='Final Exam',
                    component_type='Exam',
                    weight_percentage=60,
                    max_marks=60
                )
            )
        
        AssessmentComponent.objects.bulk_create(components, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Assessment components created'))

    def create_students(self):
        self.stdout.write('Creating 200+ students...')
        programme = Programme.objects.get(code='SC')
        intake = Intake.objects.first()
        current_year = 2024
        
        students = []
        user_counter = 1
        
        tribes = list(self.KENYAN_NAMES.keys())
        
        for i in range(220):
            tribe = random.choice(tribes)
            names = self.KENYAN_NAMES[tribe]
            first_name = random.choice(names['first'])
            last_name = random.choice(names['last'])
            
            # Generate unique number (0001-9999)
            unique_no = f"{(i % 10000):04d}"
            year = current_year - (i % 4)
            
            # Format: SC 211-0530-2022
            reg_number = f"{programme.code} {i+1:03d}-{unique_no}-{year}"
            username = f"{programme.code.lower()}{i+1:06d}"
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=f"student.{i+1}@students.uonbi.ac.ke",
                password='password123',
                first_name=first_name,
                last_name=last_name,
                user_type='Student',
                phone_number=f"+254{random.randint(7,9)}{random.randint(10000000,99999999)}",
                is_active_user=True
            )
            
            # Create student record
            year_of_study = (i % 4) + 1
            students.append(
                Student(
                    user=user,
                    registration_number=reg_number,
                    first_name=first_name,
                    last_name=last_name,
                    surname='',
                    programme=programme,
                    current_year=year_of_study,
                    intake=intake,
                    admission_date=datetime(year, 9, 15),
                    is_active=True,
                    can_upgrade=(year_of_study < 4),
                    phone=user.phone_number,
                    email=user.email,
                    date_of_birth=datetime(2000 + i % 5, random.randint(1, 12), 
                                          random.randint(1, 28)),
                    address=f"{random.randint(1, 999)} {random.choice(['Lane', 'Street', 'Road', 'Avenue'])} {tribe}",
                    parent_name=random.choice(names['first']),
                    parent_phone=f"+254{random.randint(7,9)}{random.randint(10000000,99999999)}",
                    guardian_name=random.choice(names['first']),
                    guardian_phone=f"+254{random.randint(7,9)}{random.randint(10000000,99999999)}"
                )
            )
            
            user_counter += 1
        
        Student.objects.bulk_create(students)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(students)} students created'))

    def create_fee_structures(self):
        self.stdout.write('Creating fee structures...')
        programmes = Programme.objects.all()
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        
        fee_structures = []
        for prog in programmes:
            for year_level in range(1, 5):
                fee_structures.append(
                    FeeStructure(
                        programme=prog,
                        academic_year=academic_year,
                        year_level=year_level,
                        tuition_fee=Decimal('150000'),
                        examination_fee=Decimal('5000'),
                        registration_fee=Decimal('2000'),
                        other_fees=Decimal('3000'),
                        total_fee=Decimal('160000')
                    )
                )
        
        FeeStructure.objects.bulk_create(fee_structures, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Fee structures created'))

    def create_announcements(self):
        self.stdout.write('Creating announcements...')
        programmes = Programme.objects.all()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@uonbi.ac.ke',
                password='admin123'
            )
        
        from django.utils import timezone
        
        announcements_data = [
            {
                'title': 'Welcome to Faculty of Business Portal',
                'content': 'Welcome to the Faculty of Business Management System. This portal will be your hub for all academic activities.',
                'priority': 'High',
                'days': 30
            },
            {
                'title': 'Semester Registration Portal Now Open',
                'content': 'The semester registration portal is now open. Please register for your units before the deadline.',
                'priority': 'High',
                'days': 7
            },
            {
                'title': 'Fee Payment Reminder',
                'content': 'Reminder: Please pay your tuition fees to activate your student portal account.',
                'priority': 'Medium',
                'days': 14
            },
            {
                'title': 'Examination Timetable Released',
                'content': 'The examination timetable for this semester has been released. Check your portal for details.',
                'priority': 'High',
                'days': 21
            },
            {
                'title': 'Academic Calendar Update',
                'content': 'Please note the revised academic calendar for the 2024/2025 academic year.',
                'priority': 'Medium',
                'days': 60
            },
        ]
        
        announcements = []
        for ann_data in announcements_data:
            ann = Announcement.objects.create(
                title=ann_data['title'],
                content=ann_data['content'],
                priority=ann_data['priority'],
                created_by=admin_user,
                publish_date=timezone.now(),
                expiry_date=timezone.now() + timedelta(days=ann_data['days']),
                is_published=True
            )
            ann.target_programmes.set(programmes)
            announcements.append(ann)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(announcements)} announcements created'))

    def create_events(self):
        self.stdout.write('Creating events...')
        programmes = Programme.objects.all()
        venues = Venue.objects.all()
        admin_user = User.objects.filter(username='admin').first()
        
        events_data = [
            {
                'title': 'Faculty Orientation Day',
                'type': 'Orientation',
                'date': datetime.now() + timedelta(days=5),
                'start': '09:00:00',
                'end': '12:00:00',
                'mandatory': True,
                'registration_required': True,
            },
            {
                'title': 'Leadership Summit',
                'type': 'Workshop',
                'date': datetime.now() + timedelta(days=15),
                'start': '10:00:00',
                'end': '16:00:00',
                'mandatory': False,
                'registration_required': True,
            },
            {
                'title': 'Career Fair 2024',
                'type': 'Career',
                'date': datetime.now() + timedelta(days=25),
                'start': '09:00:00',
                'end': '17:00:00',
                'mandatory': False,
                'registration_required': True,
            },
            {
                'title': 'Entrepreneurship Bootcamp',
                'type': 'Workshop',
                'date': datetime.now() + timedelta(days=35),
                'start': '08:00:00',
                'end': '18:00:00',
                'mandatory': False,
                'registration_required': True,
            },
            {
                'title': 'Research Symposium',
                'type': 'Academic',
                'date': datetime.now() + timedelta(days=45),
                'start': '09:00:00',
                'end': '15:00:00',
                'mandatory': False,
                'registration_required': False,
            },
        ]
        
        events = []
        for event_data in events_data:
            event = Event(
                title=event_data['title'],
                description=f"Join us for {event_data['title']}. This is an important event for our students.",
                event_type=event_data['type'],
                event_date=event_data['date'],
                start_time=event_data['start'],
                end_time=event_data['end'],
                venue=random.choice(venues),
                organizer=admin_user,
                is_mandatory=event_data['mandatory'],
                registration_required=event_data['registration_required'],
                max_participants=200,
            )
            event.save()
            event.target_programmes.set(programmes)
            events.append(event)
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(events)} events created'))