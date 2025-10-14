# UoN Faculty of Business Management System

A comprehensive Django-based web application for managing the Faculty of Business at the University of Nairobi (UoN). This system handles student enrollment, unit management, timetabling, grade management, fee tracking, communication, and more.

---

## 📋 Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
- [User Roles](#user-roles)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

---

## ✨ Features

### 🎓 Academic Management
- **Multi-level Programme Support**: Certificate, Diploma, Bachelor's, Master's, and PhD programmes
- **Flexible Academic Calendar**: Support for 2 or 3 semesters per year
- **Multiple Intakes**: September, January, and May intake management
- **Inter-programme Units**: Units can be shared across different programmes and year levels
- **Cross-faculty Teaching**: Track units taught by lecturers from other faculties

### 👨‍🎓 Student Management
- Complete student profiles with contact and guardian information
- Unit enrollment and semester registration
- Academic progression tracking (e.g., Bachelor's to Master's upgrades)
- Attendance tracking
- Personal academic advisor assignment

### 👨‍🏫 Lecturer Management
- Lecturer profiles with specialization and consultation hours
- Unit allocation across multiple programmes
- Marks entry and grade management
- Timetable management
- Student communication tools

### 📊 Assessment & Grading
- Flexible assessment components (CATs, Assignments, Projects, Exams, Practicals)
- Customizable grading schemes per programme
- Weighted grade calculation
- Grade approval workflow
- Academic misconduct tracking

### 📅 Timetabling
- Comprehensive timetable creation
- Venue management with capacity and facilities tracking
- Conflict detection
- Multiple programme and year level support

### 💰 Fee Management
- Programme-specific fee structures
- Semester-based billing
- Payment tracking (M-Pesa, Bank, Cash)
- Fee statement generation
- Registration eligibility based on payment status

### 📢 Communication
- Faculty-wide and targeted announcements
- Event management and registration
- Direct messaging between users
- Broadcast messaging capabilities
- Notification system

### 📚 Additional Features
- Learning resource management
- Examination timetabling
- Special exam requests
- Course evaluation by students
- Research project tracking
- Alumni records management
- Comprehensive audit logging

---

## 🔧 System Requirements

- Python 3.8+
- Django 4.2+
- PostgreSQL 12+ (recommended) or SQLite for development
- pip package manager
- Virtual environment (recommended)

### Required Python Packages

```txt
Django>=4.2
psycopg2-binary>=2.9  # For PostgreSQL
Pillow>=10.0  # For image handling
python-decouple>=3.8  # For environment variables
django-crispy-forms>=2.0  # For form styling
django-filter>=23.0  # For filtering
djangorestframework>=3.14  # For API (optional)
```

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/uon-business-faculty.git
cd uon-business-faculty
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=uon_business_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 5. Database Setup

```bash
# Create database (PostgreSQL)
psql -U postgres
CREATE DATABASE uon_business_db;
\q

# Run migrations
python manage.py makemigrations main_application
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Load Initial Data (Optional)

```bash
python manage.py loaddata initial_data.json
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000/admin` to access the admin panel.

---

## 📁 Project Structure

```
uon-business-faculty/
│
├── main_application/
│   ├── migrations/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   │   ├── main_application/
│   │   ├── base.html
│   │   └── ...
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── serializers.py
│   └── tests.py
│
├── media/
│   ├── profiles/
│   ├── announcements/
│   ├── events/
│   └── ...
│
├── static/
├── templates/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

## 🗄️ Database Models

### Core Models

#### User Management
- **User**: Extended AbstractUser with user types (Student, Lecturer, COD, Dean, ICT Admin)

#### Academic Structure
- **AcademicYear**: Academic years (e.g., 2024/2025)
- **Semester**: Semesters within academic years (1, 2, or 3)
- **Intake**: Student admission intakes
- **Department**: Departments within Faculty of Business
- **Programme**: Academic programmes (Certificate, Diploma, etc.)
- **Unit**: Academic units/courses
- **ProgrammeUnit**: Units offered in specific programmes

#### Student Management
- **Student**: Student profiles with personal and academic information
- **StudentProgression**: Track student progression between programmes
- **UnitEnrollment**: Student unit enrollments
- **SemesterRegistration**: Student semester registrations

#### Lecturer Management
- **Lecturer**: Lecturer profiles
- **UnitAllocation**: Unit assignments to lecturers

#### Assessment & Grading
- **GradingScheme**: Programme-specific grading criteria
- **AssessmentComponent**: Assessment types (CATs, Exams, etc.)
- **StudentMarks**: Individual assessment marks
- **FinalGrade**: Computed final grades

#### Timetabling
- **Venue**: Classroom/venue information
- **TimetableSlot**: Scheduled classes

#### Fee Management
- **FeeStructure**: Programme fee breakdown
- **FeePayment**: Payment records
- **FeeStatement**: Student fee statements

#### Communication
- **Announcement**: Faculty announcements
- **Event**: Faculty events
- **EventRegistration**: Student event registrations
- **Message**: Direct messaging
- **MessageReadStatus**: Message read tracking

---

## 👥 User Roles

### 1. ICT Administrator
- Full system access
- User management
- System configuration
- Database management

### 2. Dean
- Faculty-wide oversight
- Programme approval
- Budget management
- Report generation

### 3. Chairman of Department (COD)
- Department management
- Lecturer assignments
- Unit allocations
- Timetable approval

### 4. Lecturer
- Unit content management
- Marks entry
- Student communication
- Attendance tracking
- Timetable viewing

### 5. Student
- Unit enrollment
- View grades and timetable
- Fee statement viewing
- Event registration
- Message lecturers

---

## ⚙️ Configuration

### settings.py Key Configurations

```python
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main_application',
    # Add third-party apps
    'crispy_forms',
    'django_filters',
    'rest_framework',
]

# Custom User Model
AUTH_USER_MODEL = 'main_application.User'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Static Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
```

---

## 📖 Usage Guide

### For Students

#### 1. Login
```
URL: /login/
Username: Your registration number
Password: Provided by admin
```

#### 2. Enroll in Units
```
Navigate to: Dashboard → Unit Enrollment
Select semester and available units
Submit enrollment
```

#### 3. View Timetable
```
Dashboard → My Timetable
Filter by semester/week
```

#### 4. Check Grades
```
Dashboard → My Grades
Select semester
View marks breakdown
```

#### 5. Fee Statement
```
Dashboard → Fee Statement
View balance and payment history
Download statement
```

### For Lecturers

#### 1. View Allocated Units
```
Dashboard → My Units
Current semester allocations
```

#### 2. Enter Marks
```
My Units → [Select Unit] → Enter Marks
Select assessment component
Enter marks for enrolled students
Submit
```

#### 3. Manage Attendance
```
My Units → [Select Unit] → Attendance
Mark attendance for sessions
```

#### 4. Message Students
```
Dashboard → Messages → Compose
Select recipients
Send message
```

### For Administrators

#### 1. Create Academic Year
```
Admin Panel → Academic Years → Add
Set year code, dates, and mark as current
```

#### 2. Create Programme
```
Admin Panel → Programmes → Add
Set level, duration, semesters per year
```

#### 3. Allocate Units
```
Admin Panel → Unit Allocations → Add
Select unit, lecturer, semester, programmes
```

#### 4. Generate Timetable
```
Admin Panel → Timetable Slots → Add
Avoid conflicts using filters
```

---

## 🔌 API Endpoints

### Authentication
```
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/register/
```

### Students
```
GET    /api/students/
GET    /api/students/{id}/
POST   /api/students/
PUT    /api/students/{id}/
DELETE /api/students/{id}/
GET    /api/students/{id}/enrollments/
GET    /api/students/{id}/grades/
GET    /api/students/{id}/timetable/
```

### Units
```
GET    /api/units/
GET    /api/units/{id}/
GET    /api/units/{id}/students/
```

### Announcements
announcements



