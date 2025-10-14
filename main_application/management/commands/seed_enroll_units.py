from django.core.management.base import BaseCommand
from main_application.models import Student, ProgrammeUnit, UnitEnrollment, Semester

class Command(BaseCommand):
    help = "Enroll a specific student (by reg number) into all programme units not yet enrolled."

    def handle(self, *args, **options):
        reg_no = "SC001-0000-2024"

        try:
            student = Student.objects.get(registration_number=reg_no)
        except Student.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Student with reg no {reg_no} not found"))
            return

        programme = student.programme
        programme_units = ProgrammeUnit.objects.filter(programme=programme)

        if not programme_units.exists():
            self.stdout.write(self.style.WARNING(f"⚠️ No programme units found for {programme.name}"))
            return

        # Use the current semester or create one
        semester, _ = Semester.objects.get_or_create(
            academic_year__is_current=True,
            is_current=True,
            defaults={
                "semester_number": 1,
                "start_date": "2025-01-01",
                "end_date": "2025-05-30",
                "registration_deadline": "2025-01-10",
            }
        )

        created_count = 0

        for pu in programme_units:
            unit = pu.unit
            if not UnitEnrollment.objects.filter(student=student, unit=unit).exists():
                UnitEnrollment.objects.create(
                    student=student,
                    unit=unit,
                    semester=semester,
                    status="ENROLLED"
                )
                created_count += 1

        if created_count:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Enrolled {student.registration_number} into {created_count} new unit(s)."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"⚠️ {student.registration_number} is already enrolled in all programme units."
            ))
