from django.core.management.base import BaseCommand
from main_application.models import Student, ProgrammeUnit, UnitEnrollment, Semester

class Command(BaseCommand):
    help = "Enroll all students into all units of their programme across all semesters (no duplicates)."

    def handle(self, *args, **options):
        semesters = list(Semester.objects.all())
        if not semesters:
            self.stdout.write(self.style.ERROR("❌ No semesters found in the database."))
            return

        total_created = 0
        total_skipped = 0

        for student in Student.objects.select_related('programme'):
            programme = student.programme
            programme_units = ProgrammeUnit.objects.filter(programme=programme).select_related('unit')

            if not programme_units.exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠️ No units found for {student.registration_number} ({programme.name}).")
                )
                continue

            for prog_unit in programme_units:
                unit = prog_unit.unit
                year = prog_unit.year_level
                sem_number = prog_unit.semester  # this is an integer (1, 2, or 3)

                # Try to match an existing semester in DB
                semester_instance = next(
                    (sem for sem in semesters if sem.semester_number == sem_number),
                    semesters[0]  # fallback to first semester if not found
                )

                # Check if already enrolled in this unit (across any semester)
                if UnitEnrollment.objects.filter(student=student, unit=unit).exists():
                    total_skipped += 1
                    continue

                UnitEnrollment.objects.create(
                    student=student,
                    unit=unit,
                    semester=semester_instance,
                    status='ENROLLED'
                )
                total_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ {student.registration_number} enrolled in all missing units for {programme.code}."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎓 Enrollment completed!\n"
                f"✅ New enrollments created: {total_created}\n"
                f"⏩ Already enrolled (skipped): {total_skipped}\n"
            )
        )
