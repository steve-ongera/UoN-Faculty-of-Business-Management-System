import random
from datetime import timedelta, date, time, datetime

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main_application.models import Event, Venue, Programme

User = get_user_model()


class Command(BaseCommand):
    help = "Generate 10 sample UoN events with realistic data."

    def handle(self, *args, **options):
        # Delete old test events (optional)
        Event.objects.filter(title__icontains="UoN").delete()

        # Event data pool
        event_titles = [
            "UoN Annual Research Conference",
            "UoN First-Year Orientation",
            "Engineering Faculty Seminar on AI",
            "Public Health Workshop on Data Analytics",
            "Law School Moot Court Preparation Meeting",
            "Business School Entrepreneurship Forum",
            "Computer Science Hackathon",
            "Education Department Curriculum Review",
            "Medicine Clinical Skills Workshop",
            "UoN End of Semester Examination Briefing",
        ]

        event_types = [
            "CONFERENCE",
            "ORIENTATION",
            "SEMINAR",
            "WORKSHOP",
            "MEETING",
            "OTHER",
            "EXAMINATION",
        ]

        descriptions = [
            "An engaging session focusing on cutting-edge research innovations at UoN.",
            "Orientation program designed to welcome new students to the University of Nairobi.",
            "Technical seminar featuring guest speakers and faculty experts in AI and machine learning.",
            "Hands-on workshop exploring data analysis and visualization in healthcare.",
            "Meeting to prepare students for national moot court competitions.",
            "Forum encouraging student entrepreneurship and innovation across disciplines.",
            "24-hour coding marathon promoting creativity and teamwork.",
            "Panel discussion reviewing updates in the faculty’s curriculum framework.",
            "Workshop focusing on improving clinical skills for medical students.",
            "Briefing session for students regarding the upcoming final examinations.",
        ]

        venues = list(Venue.objects.all())
        if not venues:
            self.stdout.write(self.style.WARNING("⚠️ No venues found. Please add at least one venue first."))
            return

        programmes = list(Programme.objects.all())
        if not programmes:
            self.stdout.write(self.style.WARNING("⚠️ No programmes found. Please add at least one programme first."))
            return

        organizers = list(User.objects.all())
        if not organizers:
            self.stdout.write(self.style.WARNING("⚠️ No users found. Please create at least one user first."))
            return

        for i in range(10):
            title = event_titles[i]
            event_type = random.choice(event_types)
            description = descriptions[i]
            venue = random.choice(venues)
            organizer = random.choice(organizers)
            event_date = date.today() + timedelta(days=random.randint(3, 60))

            # Random start and end times
            start_hour = random.randint(8, 15)
            start_time = time(hour=start_hour, minute=0)
            end_time = (datetime.combine(event_date, start_time) + timedelta(hours=2)).time()

            # Create event
            event = Event.objects.create(
                title=title,
                description=description,
                event_type=event_type,
                venue=venue,
                event_date=event_date,
                start_time=start_time,
                end_time=end_time,
                organizer=organizer,
                is_mandatory=random.choice([True, False]),
                registration_required=random.choice([True, False]),
                max_attendees=random.choice([50, 100, 200, 500]),
                is_published=True,
            )

            # Add random target programmes
            event.target_programmes.set(random.sample(programmes, k=min(len(programmes), random.randint(1, 3))))

            self.stdout.write(self.style.SUCCESS(f"✅ Created: {event.title} ({event.event_type}) on {event.event_date}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 Successfully generated 10 sample UoN events!"))
