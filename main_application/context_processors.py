# context_processors.py
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def chatbot_context(request):
    """
    Context processor to add chatbot-related data to all templates.
    CRITICAL: Must handle all errors gracefully to prevent infinite redirect loops.
    """
    # Default safe context - always return this structure
    context = {
        'chatbot_enabled': True,
        'chatbot_available': True,
        'active_chatbot_conversation': None,
        'chatbot_unread_count': 0,
        'chatbot_user_type': 'STUDENT',
        'has_active_crisis': False,
    }
    
    # Skip processing for static files and media
    if request.path.startswith('/static/') or request.path.startswith('/media/'):
        return context
    
    # Only process for authenticated users
    if not request.user.is_authenticated:
        return context
    
    try:
        # Import models here to avoid circular imports and startup issues
        from .models import ChatbotConversation
        
        # Get user type safely
        try:
            context['chatbot_user_type'] = getattr(request.user, 'user_type', 'GUEST')
        except Exception as e:
            logger.warning(f"Error getting user_type: {e}")
            context['chatbot_user_type'] = 'GUEST'
        
        # Get active conversation - with error handling
        try:
            active_conversation = ChatbotConversation.objects.filter(
                user=request.user,
                status='ACTIVE'
            ).select_related('user').first()
            
            context['active_chatbot_conversation'] = active_conversation
            
            # Get unread message count only if conversation exists
            if active_conversation:
                try:
                    unread_count = active_conversation.messages.filter(
                        message_type='AI',
                        was_helpful__isnull=True
                    ).count()
                    context['chatbot_unread_count'] = unread_count
                except Exception as e:
                    logger.warning(f"Error counting unread messages: {e}")
                    context['chatbot_unread_count'] = 0
        
        except Exception as e:
            logger.warning(f"Error fetching active conversation for user {request.user.id}: {e}")
            context['active_chatbot_conversation'] = None
            context['chatbot_unread_count'] = 0
        
        # Check for crisis alerts - with error handling
        try:
            if hasattr(request.user, 'student_profile'):
                student_profile = request.user.student_profile
                
                # Check if crisis_alerts relationship exists
                if hasattr(student_profile, 'crisis_alerts'):
                    recent_crisis = student_profile.crisis_alerts.filter(
                        status__in=['DETECTED', 'NOTIFIED', 'IN_PROGRESS']
                    ).exists()
                    context['has_active_crisis'] = recent_crisis
                else:
                    context['has_active_crisis'] = False
            else:
                context['has_active_crisis'] = False
        
        except AttributeError as e:
            logger.warning(f"Error checking crisis alerts (likely student_profile doesn't exist): {e}")
            context['has_active_crisis'] = False
        
        except Exception as e:
            logger.warning(f"Error checking crisis alerts for user {request.user.id}: {e}")
            context['has_active_crisis'] = False
    
    except Exception as e:
        # Critical error - log it but don't break the request
        logger.error(f"Critical error in chatbot_context processor: {e}", exc_info=True)
        # Return safe defaults
        pass
    
    return context