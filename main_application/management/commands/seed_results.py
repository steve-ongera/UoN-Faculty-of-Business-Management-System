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
    help = "Seed exam results for the first 50 students across all enrolled units."

    def handle(self, *args, **options):
        # Pick the first 50 students
        students = Student.objects.all()[:50]
        lecturers = list(Lecturer.objects.all())

        if not students.exists():
            self.stdout.write(self.style.ERROR("❌ No students found."))
            return
        if not lecturers:
            self.stdout.write(self.style.ERROR("❌ No lecturers available to assign marks."))
            return

        created_marks = 0
        created_grades = 0
        skipped = 0

        for student in students:
            enrollments = UnitEnrollment.objects.filter(student=student)

            if not enrollments.exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠️ {student.registration_number} has no enrollments.")
                )
                continue

            for enrollment in enrollments:
                # Get or create the exam component for this unit
                exam_components = AssessmentComponent.objects.filter(
                    unit=enrollment.unit, component_type="EXAM"
                )

                if not exam_components.exists():
                    # If no exam component exists, create one
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
                    marks = Decimal(random.randint(30, 95))  # random realistic mark

                    StudentMarks.objects.create(
                        enrollment=enrollment,
                        assessment_component=component,
                        marks_obtained=marks,
                        entered_by=entered_by,
                        remarks="Auto-seeded exam result",
                    )
                    created_marks += 1

                    # Compute grade immediately
                    grade, points = self.compute_grade(marks)

                    # Skip if grade exists
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
                    f"✅ Seeded results for {student.registration_number}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎯 Results Seeding Completed!\n"
                f"✅ Marks created: {created_marks}\n"
                f"✅ Grades created: {created_grades}\n"
                f"⏩ Skipped (existing): {skipped}\n"
            )
        )

    def compute_grade(self, total_marks):
        """Compute grade and grade point based on total marks"""
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
