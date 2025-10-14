from django.core.management.base import BaseCommand
from main_application.models import Department, Programme, Unit, ProgrammeUnit
from django.db import transaction
import random

class Command(BaseCommand):
    help = "Seed units and programme units for all programmes."

    @transaction.atomic
    def handle(self, *args, **options):
        departments = Department.objects.all()
        programmes = Programme.objects.all()

        if not departments.exists() or not programmes.exists():
            self.stdout.write(self.style.ERROR("❌ Please ensure Departments and Programmes exist before seeding units."))
            return

        unit_count_before = Unit.objects.count()
        programme_unit_count_before = ProgrammeUnit.objects.count()

        self.stdout.write(self.style.NOTICE("🚀 Starting unit seeding process...\n"))

        # Predefined sample unit names (you can expand these)
        base_unit_names = [
            # 🧑‍💻 Computer Science & IT
            "Introduction to Computer Science", "Programming Fundamentals", "Data Structures and Algorithms",
            "Database Systems", "Computer Networks", "Operating Systems", "Software Engineering",
            "Web Application Development", "Mobile Application Development", "Cloud Computing",
            "Cybersecurity Fundamentals", "Artificial Intelligence", "Machine Learning",
            "Deep Learning", "Data Mining", "Human-Computer Interaction", "Computer Graphics",
            "Systems Analysis and Design", "Internet of Things (IoT)", "Big Data Analytics",
            "Blockchain Technology", "Ethical Hacking", "Distributed Systems", "Embedded Systems",
            "Computer Architecture", "Parallel Computing", "Compiler Construction", "Natural Language Processing",
            "Information Security Management", "IT Project Management", "Network Administration",
            "Digital Forensics", "Computer Vision", "Data Visualization", "Advanced Programming in Python",
            "Object-Oriented Programming with Java", "C++ Programming", "Web Security", "Quantum Computing",

            # 💼 Business & Management
            "Principles of Management", "Business Communication", "Financial Accounting",
            "Cost Accounting", "Managerial Economics", "Marketing Principles", "Strategic Management",
            "Entrepreneurship Development", "Human Resource Management", "Operations Management",
            "Organizational Behavior", "Corporate Finance", "Business Law", "E-Commerce",
            "International Business", "Supply Chain Management", "Project Management",
            "Investment Analysis", "Business Ethics", "Taxation and Auditing",
            "Sales and Marketing Strategies", "Risk Management", "Customer Relationship Management",
            "Performance Management Systems", "Business Intelligence", "Microeconomics", "Macroeconomics",

            # 📊 Statistics, Mathematics, and Economics
            "Introduction to Statistics", "Probability Theory", "Linear Algebra",
            "Calculus I", "Calculus II", "Statistical Inference", "Regression Analysis",
            "Econometrics", "Operations Research", "Mathematical Modelling",
            "Numerical Methods", "Quantitative Techniques", "Actuarial Mathematics",
            "Financial Mathematics", "Time Series Analysis",

            # ⚙️ Engineering & Technology
            "Engineering Mathematics", "Engineering Drawing", "Electrical Circuits",
            "Electronics Fundamentals", "Control Systems", "Thermodynamics",
            "Fluid Mechanics", "Strength of Materials", "Mechanical Design",
            "Manufacturing Technology", "Engineering Workshop Practice",
            "Industrial Automation", "Renewable Energy Systems",
            "Environmental Engineering", "Digital Signal Processing",
            "Instrumentation and Measurement", "Power Systems Analysis",
            "Telecommunication Systems", "Civil Engineering Materials",
            "Structural Analysis", "Transportation Engineering",

            # 🧬 Science & Health
            "General Chemistry", "Organic Chemistry", "Inorganic Chemistry",
            "Biochemistry", "Physics I", "Physics II", "Cell Biology",
            "Genetics", "Microbiology", "Molecular Biology", "Anatomy and Physiology",
            "Public Health", "Pharmacology", "Pathophysiology", "Health Informatics",
            "Epidemiology", "Biostatistics", "Nutrition and Dietetics",
            "Medical Laboratory Science", "Immunology", "Environmental Health",

            # 🧠 Social Sciences & Humanities
            "Introduction to Psychology", "Developmental Psychology", "Sociology of Education",
            "Introduction to Sociology", "Philosophy and Logic", "Anthropology", "Criminology",
            "Political Science", "Public Administration", "International Relations",
            "Ethics and Society", "Gender Studies", "Mass Communication",
            "Media Studies", "Public Speaking", "Research Methods in Social Science",

            # 📚 Education
            "Foundations of Education", "Educational Psychology", "Curriculum Development",
            "Instructional Technology", "Measurement and Evaluation", "Classroom Management",
            "Special Needs Education", "Educational Administration", "Guidance and Counselling",
            "Teaching Methods", "Educational Research", "Child Development",

            # 🎨 Arts, Design & Creative Studies
            "Introduction to Art and Design", "Graphic Design Fundamentals",
            "Photography and Imaging", "Creative Writing", "Music Theory",
            "Drama and Theatre Studies", "Film Production", "Animation and Motion Graphics",
            "Interior Design", "Fashion Design and Textile Studies",
            "Digital Illustration", "Media Production", "Visual Communication Design",
            "3D Modeling and Animation", "Performing Arts",

            # 🌍 Environment & Agriculture
            "Introduction to Environmental Science", "Soil Science", "Crop Production",
            "Agricultural Economics", "Animal Husbandry", "Agroforestry",
            "Climate Change and Adaptation", "Water Resource Management",
            "Waste Management", "Sustainable Agriculture", "Food Science and Technology",
            "Agricultural Extension and Communication",

            # ⚖️ Law & Governance
            "Constitutional Law", "Criminal Law", "Law of Torts", "Contract Law",
            "Administrative Law", "International Law", "Labour Law",
            "Legal Ethics", "Intellectual Property Law", "Environmental Law",
            "Commercial Law", "Law of Evidence", "Company Law",

            # 💊 Nursing & Medicine
            "Nursing Foundations", "Clinical Pharmacology", "Medical-Surgical Nursing",
            "Community Health Nursing", "Pediatric Nursing", "Obstetric Nursing",
            "Psychiatric Nursing", "Emergency and Critical Care", "Anatomy and Physiology II",
            "Health Assessment", "Nursing Leadership", "Research in Nursing",
            "Nursing Informatics"
        ]


        # Ensure every department has at least some units
        for dept in departments:
            for i in range(5):  # Add 5 random units per department if not already existing
                unit_name = random.choice(base_unit_names)
                unit_code = f"{dept.code.upper()}U{random.randint(100,999)}"
                if not Unit.objects.filter(code=unit_code).exists():
                    Unit.objects.create(
                        code=unit_code,
                        name=unit_name,
                        description=f"This is a unit about {unit_name.lower()} in the {dept.name} department.",
                        department=dept,
                        credit_hours=random.choice([2, 3, 4]),
                        is_core=random.choice([True, False]),
                    )

        self.stdout.write(self.style.SUCCESS(f"✅ Units seeded successfully. Total units: {Unit.objects.count()}"))

        # Now assign units to each programme
        all_units = list(Unit.objects.all())

        for programme in programmes:
            total_years = programme.duration_years
            semesters_per_year = programme.semesters_per_year
            dept_units = [u for u in all_units if u.department == programme.department]

            if not dept_units:
                self.stdout.write(self.style.WARNING(f"⚠️ No units found for {programme.name}. Skipping..."))
                continue

            for year in range(1, total_years + 1):
                for sem in range(1, semesters_per_year + 1):
                    # Check if this semester already has units
                    existing_units = ProgrammeUnit.objects.filter(programme=programme, year_level=year, semester=sem)
                    if existing_units.exists():
                        self.stdout.write(self.style.NOTICE(f"⏭️  Skipping {programme.code} Year {year} Sem {sem} (already populated)."))
                        continue

                    # Pick 4–6 random units from the department
                    new_units = random.sample(dept_units, min(len(dept_units), random.randint(4, 6)))

                    for unit in new_units:
                        ProgrammeUnit.objects.create(
                            programme=programme,
                            unit=unit,
                            year_level=year,
                            semester=sem,
                            is_mandatory=random.choice([True, False])
                        )

                    self.stdout.write(self.style.SUCCESS(f"✅ Added {len(new_units)} units for {programme.code} Year {year} Sem {sem}"))

        unit_count_after = Unit.objects.count()
        programme_unit_count_after = ProgrammeUnit.objects.count()

        self.stdout.write(self.style.SUCCESS("\n🎯 Seeding Completed Successfully!"))
        self.stdout.write(self.style.SUCCESS(f"📘 New Units Added: {unit_count_after - unit_count_before}"))
        self.stdout.write(self.style.SUCCESS(f"📗 Programme Units Added: {programme_unit_count_after - programme_unit_count_before}"))
