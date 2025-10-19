# management/commands/update_chatbot_analytics.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg
from datetime import datetime, timedelta
from main_application.models import (
    ChatbotAnalytics, ChatbotConversation, ChatMessage,
    CrisisAlert
)


class Command(BaseCommand):
    help = 'Update daily chatbot analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to update analytics for (YYYY-MM-DD)',
        )

    def handle(self, *args, **options):
        if options['date']:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date()

        self.stdout.write(f'Updating analytics for {target_date}...')

        # Get or create analytics record
        analytics, created = ChatbotAnalytics.objects.get_or_create(
            date=target_date,
            defaults={
                'total_conversations': 0,
                'total_messages': 0,
                'unique_users': 0,
            }
        )

        # Set time boundaries
        start_time = timezone.datetime.combine(target_date, timezone.datetime.min.time())
        end_time = timezone.datetime.combine(target_date, timezone.datetime.max.time())
        
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        if timezone.is_naive(end_time):
            end_time = timezone.make_aware(end_time)

        # Count conversations
        conversations = ChatbotConversation.objects.filter(
            started_at__range=[start_time, end_time]
        )
        analytics.total_conversations = conversations.count()

        # Count messages
        messages = ChatMessage.objects.filter(
            created_at__range=[start_time, end_time]
        )
        analytics.total_messages = messages.count()

        # Count unique users
        analytics.unique_users = conversations.values('user').distinct().count()

        # Count by conversation type
        analytics.academic_conversations = conversations.filter(
            conversation_type='ACADEMIC'
        ).count()
        
        analytics.mental_health_conversations = conversations.filter(
            conversation_type='MENTAL_HEALTH'
        ).count()
        
        analytics.general_conversations = conversations.filter(
            conversation_type='GENERAL'
        ).count()

        # Count by sentiment
        analytics.positive_sentiment_count = messages.filter(
            sentiment='POSITIVE'
        ).count()
        
        analytics.neutral_sentiment_count = messages.filter(
            sentiment='NEUTRAL'
        ).count()
        
        analytics.negative_sentiment_count = messages.filter(
            sentiment__in=['NEGATIVE', 'ANXIOUS', 'DEPRESSED']
        ).count()
        
        analytics.crisis_detected_count = messages.filter(
            is_crisis=True
        ).count()

        # Calculate averages
        avg_response = conversations.aggregate(avg=Avg('avg_response_time_seconds'))['avg']
        analytics.avg_response_time = avg_response or 0.0

        avg_satisfaction = conversations.filter(
            user_satisfaction__isnull=False
        ).aggregate(avg=Avg('user_satisfaction'))['avg']
        analytics.avg_satisfaction_rating = avg_satisfaction

        # Count escalations
        analytics.escalated_conversations = conversations.filter(
            escalated=True
        ).count()

        # Save analytics
        analytics.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated analytics for {target_date}\n'
                f'Conversations: {analytics.total_conversations}\n'
                f'Messages: {analytics.total_messages}\n'
                f'Unique Users: {analytics.unique_users}'
            )
        )


# management/commands/cleanup_old_conversations.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main_application.models import ChatbotConversation


class Command(BaseCommand):
    help = 'Archive old chatbot conversations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep conversations (default: 90)',
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(f'Archiving conversations older than {days} days...')

        # Find conversations to archive
        old_conversations = ChatbotConversation.objects.filter(
            last_message_at__lt=cutoff_date,
            status__in=['CLOSED']
        ).exclude(status='ARCHIVED')

        count = old_conversations.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No conversations to archive'))
            return

        # Archive conversations
        old_conversations.update(status='ARCHIVED')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully archived {count} conversations')
        )


# management/commands/populate_knowledge_base.py
from django.core.management.base import BaseCommand
from main_application.models import ChatbotKnowledgeBase


class Command(BaseCommand):
    help = 'Populate chatbot knowledge base with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Populating knowledge base...')

        knowledge_base_data = [
            {
                'category': 'ACADEMIC',
                'question': 'How do I check my timetable?',
                'answer': 'You can view your timetable by going to the Timetable section in your student portal. It shows all your classes, venues, and times for the current semester.',
                'keywords': ['timetable', 'schedule', 'classes', 'time'],
            },
            {
                'category': 'ACADEMIC',
                'question': 'How do I register for units?',
                'answer': 'Unit registration is done at the beginning of each semester through the Registration section. You must clear your fees before you can register. Select the units for your year level and semester, then submit your registration.',
                'keywords': ['register', 'units', 'enrollment', 'courses'],
            },
            {
                'category': 'FEES',
                'question': 'How do I check my fee balance?',
                'answer': 'Go to the Fees section in your portal to view your current fee balance, payment history, and fee structure for your programme.',
                'keywords': ['fees', 'balance', 'payment', 'tuition'],
            },
            {
                'category': 'FEES',
                'question': 'What payment methods are accepted?',
                'answer': 'We accept M-Pesa, bank deposits, and direct bank transfers. Use your registration number as the payment reference.',
                'keywords': ['payment', 'mpesa', 'bank', 'pay'],
            },
            {
                'category': 'GRADES',
                'question': 'When are exam results released?',
                'answer': 'Exam results are typically released 4-6 weeks after the examination period ends. You will receive a notification when your results are available in the Grades section.',
                'keywords': ['results', 'grades', 'marks', 'exam', 'scores'],
            },
            {
                'category': 'GRADES',
                'question': 'How is my GPA calculated?',
                'answer': 'Your GPA is calculated by multiplying each unit\'s grade point by its credit hours, summing these values, and dividing by the total credit hours attempted.',
                'keywords': ['gpa', 'calculation', 'grade point', 'average'],
            },
            {
                'category': 'REGISTRATION',
                'question': 'What is the registration deadline?',
                'answer': 'Registration deadlines are set at the beginning of each semester. Check the Academic Calendar or your student portal for the exact date. Late registration may incur penalties.',
                'keywords': ['deadline', 'last day', 'registration', 'when'],
            },
            {
                'category': 'MENTAL_HEALTH',
                'question': 'I\'m feeling stressed about exams',
                'answer': 'It\'s normal to feel stressed during exams. Try these tips:\n\n1. Break study sessions into manageable chunks\n2. Take regular breaks\n3. Get adequate sleep\n4. Exercise regularly\n5. Talk to someone\n\nIf stress becomes overwhelming, our Counseling Center is here to help. Would you like me to connect you with a counselor?',
                'keywords': ['stress', 'exam', 'anxiety', 'worried'],
            },
            {
                'category': 'MENTAL_HEALTH',
                'question': 'Where can I get counseling services?',
                'answer': 'The University Counseling Center is located in the Main Administration Block, 2nd Floor. Services are:\n\n• Available 24/7 for emergencies\n• Walk-in hours: Mon-Fri 9AM-5PM\n• Appointments: counseling@university.ac.ke\n• Hotline: +254XXXXXXXXX\n\nAll services are confidential and free for students.',
                'keywords': ['counseling', 'therapy', 'mental health', 'help'],
            },
            {
                'category': 'GENERAL',
                'question': 'How do I contact my lecturer?',
                'answer': 'You can find your lecturer\'s contact information and consultation hours in the Timetable section or contact the department office.',
                'keywords': ['lecturer', 'contact', 'teacher', 'professor'],
            },
        ]

        created_count = 0
        updated_count = 0

        for data in knowledge_base_data:
            kb, created = ChatbotKnowledgeBase.objects.get_or_create(
                category=data['category'],
                question=data['question'],
                defaults={
                    'answer': data['answer'],
                    'keywords': data['keywords'],
                    'is_active': True,
                    'priority': 0,
                }
            )

            if created:
                created_count += 1
            else:
                kb.answer = data['answer']
                kb.keywords = data['keywords']
                kb.save()
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Knowledge base populated!\n'
                f'Created: {created_count} entries\n'
                f'Updated: {updated_count} entries'
            )
        )


# management/commands/send_crisis_notifications.py
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from main_application.models import CrisisAlert, User


class Command(BaseCommand):
    help = 'Send notifications for unhandled crisis alerts'

    def handle(self, *args, **options):
        self.stdout.write('Checking for unhandled crisis alerts...')

        # Get unhandled critical alerts
        unhandled_alerts = CrisisAlert.objects.filter(
            status='DETECTED',
            severity='CRITICAL',
            authorities_notified=False
        )

        if not unhandled_alerts.exists():
            self.stdout.write(self.style.SUCCESS('No unhandled crisis alerts'))
            return

        # Get staff to notify
        staff = User.objects.filter(
            user_type__in=['DEAN', 'COD', 'ICT_ADMIN'],
            is_active=True
        )

        for alert in unhandled_alerts:
            # Send email notifications
            subject = f'URGENT: Crisis Alert - {alert.student.registration_number}'
            message = f"""
URGENT CRISIS ALERT

Student: {alert.student.first_name} {alert.student.last_name}
Registration Number: {alert.student.registration_number}
Programme: {alert.student.programme.name}

Crisis Type: {alert.get_crisis_type_display()}
Severity: {alert.severity}
Detected: {alert.detected_at}

Keywords Detected: {', '.join(alert.detected_keywords)}

IMMEDIATE ACTION REQUIRED

Please contact the student immediately at:
Phone: {alert.student.phone or 'Not provided'}
Parent: {alert.student.parent_phone or 'Not provided'}

View full conversation: {settings.SITE_URL}/chatbot/conversation/{alert.conversation.conversation_id}/

This is an automated alert from the Student Support AI System.
            """

            # Send to staff
            recipient_list = [user.email for user in staff if user.email]
            
            if recipient_list:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=False,
                )

            # Mark as notified
            alert.authorities_notified = True
            alert.notification_sent_at = timezone.now()
            alert.notified_users.set(staff)
            alert.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Sent notification for {alert.student.registration_number}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Processed {unhandled_alerts.count()} crisis alerts'
            )
        )