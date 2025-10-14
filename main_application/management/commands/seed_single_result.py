import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from main_application.models import (
    Student,
    UnitEnrollment,
    AssessmentComponent,
    StudentMarks,
    FinalGrade,
    Lecturer,
)

class Command(BaseCommand):
    help = "Seed EXAM results for a single student (e.g. SC001-0000-2024)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reg',
            type=str,
            help='Registration number of the student (e.g. SC001-0000-2024)',
            required=True
        )

    def handle(self, *args, **options):
        reg_no = options['reg']
        try:
            student = Student.objects.get(registration_number=reg_no)
        except Student.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Student {reg_no} not found."))
            return

        lecturers = list(Lecturer.objects.all())
        if not lecturers:
            self.stdout.write(self.style.ERROR("❌ No lecturers found. Add at least one lecturer first."))
            return

        enrollments = UnitEnrollment.objects.filter(student=student)
        if not enrollments.exists():
            self.stdout.write(self.style.WARNING(f"⚠️ {reg_no} has no enrolled units."))
            return

        created_marks = 0
        created_grades = 0
        skipped = 0

        self.stdout.write(self.style.SUCCESS(f"📘 Seeding exam results for {student.registration_number} ..."))

        for enrollment in enrollments:
            # Get or create EXAM component for this unit
            exam_components = AssessmentComponent.objects.filter(
                unit=enrollment.unit, component_type="EXAM"
            )

            if not exam_components.exists():
                exam_components = [
                    AssessmentComponent.objects.create(
                        unit=enrollment.unit,
                        name="Final Exam",
                        component_type="EXAM",
                        weight_percentage=Decimal("70.00"),
                        max_marks=Decimal("100.00"),
                    )
                ]

            for component in exam_components:
                # Skip if marks already exist
                if StudentMarks.objects.filter(
                    enrollment=enrollment, assessment_component=component
                ).exists():
                    skipped += 1
                    continue

                entered_by = random.choice(lecturers)
                marks = Decimal(random.randint(35, 95))

                StudentMarks.objects.create(
                    enrollment=enrollment,
                    assessment_component=component,
                    marks_obtained=marks,
                    entered_by=entered_by,
                    remarks="Auto-seeded exam mark",
                )
                created_marks += 1

                # Compute final grade
                grade, points = self.compute_grade(marks)

                # Skip if grade already exists
                if FinalGrade.objects.filter(enrollment=enrollment).exists():
                    skipped += 1
                    continue

                FinalGrade.objects.create(
                    enrollment=enrollment,
                    total_marks=marks,
                    grade=grade,
                    grade_point=points,
                    computed_date=timezone.now(),
                    approved_by=entered_by,
                    is_approved=True,
                )
                created_grades += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎯 Seeding Complete for {reg_no}\n"
                f"✅ Marks created: {created_marks}\n"
                f"✅ Grades created: {created_grades}\n"
                f"⏩ Skipped (already existed): {skipped}\n"
            )
        )

    def compute_grade(self, total_marks):
        """Simple grading logic."""
        if total_marks >= 70:
            return "A", Decimal("4.00")
        elif total_marks >= 60:
            return "B", Decimal("3.00")
        elif total_marks >= 50:
            return "C", Decimal("2.00")
        elif total_marks >= 40:
            return "D", Decimal("1.00")
        else:
            return "E", Decimal("0.00")
