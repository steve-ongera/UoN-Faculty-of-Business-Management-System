# templatetags/chatbot_tags.py
from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import timedelta

register = template.Library()


@register.inclusion_tag('chatbot/chatbot_widget.html', takes_context=True)
def chatbot_widget(context):
    """
    Render the floating chatbot widget
    Usage: {% chatbot_widget %}
    """
    request = context['request']
    user = request.user
    
    widget_data = {
        'user': user,
        'is_authenticated': user.is_authenticated,
        'active_conversation': None,
        'unread_count': 0,
        'user_type': getattr(user, 'user_type', 'GUEST'),
        'has_crisis_alert': False,
    }
    
    if user.is_authenticated:
        # Get active conversation
        if hasattr(request, 'active_chatbot_conversation'):
            widget_data['active_conversation'] = request.active_chatbot_conversation
        
        # Check for crisis alerts
        if hasattr(request, 'has_crisis_alert'):
            widget_data['has_crisis_alert'] = request.has_crisis_alert
        
        # Get student info if applicable
        if hasattr(user, 'student_profile'):
            widget_data['student'] = user.student_profile
    
    return widget_data


@register.filter
def chatbot_sentiment_icon(sentiment):
    """
    Return appropriate icon for sentiment
    Usage: {{ message.sentiment|chatbot_sentiment_icon }}
    """
    icons = {
        'POSITIVE': '😊',
        'NEUTRAL': '😐',
        'NEGATIVE': '😟',
        'ANXIOUS': '😰',
        'DEPRESSED': '😢',
        'CRISIS': '🆘',
    }
    return icons.get(sentiment, '💬')


@register.filter
def chatbot_sentiment_color(sentiment):
    """
    Return appropriate color class for sentiment
    Usage: {{ message.sentiment|chatbot_sentiment_color }}
    """
    colors = {
        'POSITIVE': 'text-green-600',
        'NEUTRAL': 'text-gray-600',
        'NEGATIVE': 'text-orange-600',
        'ANXIOUS': 'text-yellow-600',
        'DEPRESSED': 'text-blue-600',
        'CRISIS': 'text-red-600',
    }
    return colors.get(sentiment, 'text-gray-600')


@register.filter
def chatbot_risk_badge(risk_level):
    """
    Return appropriate badge HTML for risk level
    Usage: {{ assessment.risk_level|chatbot_risk_badge }}
    """
    badges = {
        'MINIMAL': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Minimal</span>',
        'MILD': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">Mild</span>',
        'MODERATE': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">Moderate</span>',
        'SEVERE': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">Severe</span>',
        'CRITICAL': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Critical</span>',
    }
    return mark_safe(badges.get(risk_level, ''))


@register.filter
def chatbot_conversation_type_icon(conv_type):
    """
    Return icon for conversation type
    Usage: {{ conversation.conversation_type|chatbot_conversation_type_icon }}
    """
    icons = {
        'ACADEMIC': '📚',
        'MENTAL_HEALTH': '🧠',
        'GENERAL': '💬',
        'REGISTRATION': '📝',
        'FEES': '💰',
        'TIMETABLE': '📅',
        'GRADES': '📊',
        'CAREER': '🎯',
        'EMERGENCY': '🆘',
    }
    return icons.get(conv_type, '💬')


@register.filter
def time_ago(timestamp):
    """
    Return human-readable time difference
    Usage: {{ message.created_at|time_ago }}
    """
    if not timestamp:
        return ''
    
    now = timezone.now()
    diff = now - timestamp
    
    if diff < timedelta(minutes=1):
        return 'Just now'
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif diff < timedelta(days=7):
        days = diff.days
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        return timestamp.strftime('%b %d, %Y')


@register.simple_tag
def chatbot_quick_actions():
    """
    Return list of quick action buttons for chatbot
    Usage: {% chatbot_quick_actions %}
    """
    return [
        {'label': 'Check Timetable', 'action': 'timetable', 'icon': '📅'},
        {'label': 'View Grades', 'action': 'grades', 'icon': '📊'},
        {'label': 'Fee Balance', 'action': 'fees', 'icon': '💰'},
        {'label': 'Registration', 'action': 'registration', 'icon': '📝'},
        {'label': 'Need Support', 'action': 'mental_health', 'icon': '🤗'},
    ]


@register.filter
def chatbot_message_class(message_type):
    """
    Return CSS class for message bubble
    Usage: {{ message.message_type|chatbot_message_class }}
    """
    classes = {
        'USER': 'bg-blue-600 text-white ml-auto',
        'AI': 'bg-gray-200 text-gray-900 mr-auto',
        'SYSTEM': 'bg-yellow-100 text-yellow-900 mx-auto text-center',
        'HUMAN': 'bg-green-100 text-green-900 mr-auto',
    }
    return classes.get(message_type, 'bg-gray-100 text-gray-900')


@register.simple_tag(takes_context=True)
def chatbot_unread_count(context):
    """
    Get unread message count for current user
    Usage: {% chatbot_unread_count %}
    """
    from ..models import ChatbotConversation
    
    request = context['request']
    if not request.user.is_authenticated:
        return 0
    
    active_conv = ChatbotConversation.objects.filter(
        user=request.user,
        status='ACTIVE'
    ).first()
    
    if not active_conv:
        return 0
    
    # Count AI messages that haven't been rated
    unread = active_conv.messages.filter(
        message_type='AI',
        was_helpful__isnull=True
    ).count()
    
    return unread


@register.inclusion_tag('chatbot/crisis_banner.html', takes_context=True)
def crisis_alert_banner(context):
    """
    Display crisis alert banner if active
    Usage: {% crisis_alert_banner %}
    """
    request = context['request']
    
    return {
        'show_banner': hasattr(request, 'critical_crisis_alert'),
        'alert': getattr(request, 'critical_crisis_alert', None),
    }


@register.filter
def format_phone_number(phone):
    """
    Format phone number for display
    Usage: {{ phone|format_phone_number }}
    """
    if not phone:
        return ''
    
    # Remove non-numeric characters
    cleaned = ''.join(filter(str.isdigit, str(phone)))
    
    # Format as +254 XXX XXX XXX
    if cleaned.startswith('254') and len(cleaned) == 12:
        return f'+254 {cleaned[3:6]} {cleaned[6:9]} {cleaned[9:]}'
    elif cleaned.startswith('0') and len(cleaned) == 10:
        return f'+254 {cleaned[1:4]} {cleaned[4:7]} {cleaned[7:]}'
    
    return phone


@register.simple_tag
def get_mental_health_resources():
    """
    Get mental health resources
    Usage: {% get_mental_health_resources %}
    """
    return {
        'emergency': [
            {'name': 'Emergency Services', 'number': '999', 'available': '24/7'},
            {'name': 'Kenya Red Cross', 'number': '1199', 'available': '24/7'},
            {'name': 'Befrienders Kenya', 'number': '+254 722 178 177', 'available': '24/7'},
        ],
        'campus': [
            {'name': 'University Counseling Center', 'available': '24/7'},
            {'name': 'Dean of Students Office', 'available': 'Mon-Fri 8AM-5PM'},
            {'name': 'Student Wellness Office', 'available': 'Mon-Fri 9AM-5PM'},
        ],
        'online': [
            {'name': 'Mental Health Kenya', 'url': 'https://mentalhealthkenya.org'},
            {'name': 'KEMRI Wellcome Trust', 'url': 'https://kemri-wellcome.org'},
        ]
    }


@register.filter
def chatbot_status_badge(status):
    """
    Return status badge HTML
    Usage: {{ conversation.status|chatbot_status_badge }}
    """
    badges = {
        'ACTIVE': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">Active</span>',
        'CLOSED': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">Closed</span>',
        'ESCALATED': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">Escalated</span>',
        'ARCHIVED': '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-600">Archived</span>',
    }
    return mark_safe(badges.get(status, ''))


@register.filter
def percentage(value, total):
    """
    Calculate percentage
    Usage: {{ value|percentage:total }}
    """
    if not total or total == 0:
        return 0
    return round((value / total) * 100, 1)


@register.simple_tag
def chatbot_stats_summary(user):
    """
    Get chatbot statistics summary for user
    Usage: {% chatbot_stats_summary user %}
    """
    from ..models import ChatbotConversation, ChatMessage
    from django.db.models import Count, Avg
    
    conversations = ChatbotConversation.objects.filter(user=user)
    
    stats = {
        'total_conversations': conversations.count(),
        'total_messages': ChatMessage.objects.filter(
            conversation__user=user,
            message_type='USER'
        ).count(),
        'avg_satisfaction': conversations.filter(
            user_satisfaction__isnull=False
        ).aggregate(avg=Avg('user_satisfaction'))['avg'] or 0,
    }
    
    return stats