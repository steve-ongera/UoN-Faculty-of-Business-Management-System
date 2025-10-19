# context_processors.py
from django.utils import timezone
from .models import ChatbotConversation, SystemSettings

def chatbot_context(request):
    """
    Context processor to add chatbot-related data to all templates
    """
    context = {
        'chatbot_enabled': True,
        'chatbot_available': True,
    }
    
    if request.user.is_authenticated:
        # Get active conversation for current user
        active_conversation = ChatbotConversation.objects.filter(
            user=request.user,
            status='ACTIVE'
        ).first()
        
        # Get unread message count (if applicable)
        unread_count = 0
        if active_conversation:
            unread_count = active_conversation.messages.filter(
                message_type='AI',
                was_helpful__isnull=True
            ).count()
        
        context.update({
            'active_chatbot_conversation': active_conversation,
            'chatbot_unread_count': unread_count,
            'chatbot_user_type': request.user.user_type,
        })
        
        # Check for crisis alerts
        if hasattr(request.user, 'student_profile'):
            recent_crisis = request.user.student_profile.crisis_alerts.filter(
                status__in=['DETECTED', 'NOTIFIED', 'IN_PROGRESS']
            ).exists()
            context['has_active_crisis'] = recent_crisis
    
    return context