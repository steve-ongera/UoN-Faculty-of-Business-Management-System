"""
Security Middleware for automatic audit logging and security monitoring.
Place this file in your app directory as middleware.py
"""

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from .models import (
    AuditLog, SecurityEvent, LoginAttempt, UserSession, 
    BlockedIP, SystemSettings, User
)
from .utils import (
    get_client_ip, get_user_agent, get_request_path, 
    parse_user_agent, is_ip_blocked, log_security_event
)
import json


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to handle security features:
    - IP blocking
    - Maintenance mode
    - Session tracking
    - Automatic audit logging
    """
    
    def process_request(self, request):
        """Process incoming requests for security checks"""
        
        # Get client IP
        ip_address = get_client_ip(request)
        
        # Check if IP is blocked
        if ip_address:
            is_blocked, blocked_ip = is_ip_blocked(ip_address)
            if is_blocked:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    f"Access denied. Your IP address has been blocked. "
                    f"Reason: {blocked_ip.reason}"
                )
        
        # Check maintenance mode (allow superusers and ICT admins)
        settings = SystemSettings.get_settings()
        if settings.maintenance_mode:
            if request.user.is_authenticated:
                if not (request.user.is_superuser or 
                       getattr(request.user, 'user_type', '') == 'ICT_ADMIN'):
                    from django.shortcuts import render
                    return render(request, 'maintenance.html', {
                        'message': settings.maintenance_message
                    })
            else:
                # Not authenticated - show maintenance page unless accessing login
                if not request.path.startswith('/admin/') and request.path != '/login/':
                    from django.shortcuts import render
                    return render(request, 'maintenance.html', {
                        'message': settings.maintenance_message
                    })
        
        # Track session activity
        if request.user.is_authenticated:
            self.update_session_activity(request)
        
        # Store request start time for performance monitoring
        request.start_time = timezone.now()
        
        return None
    
    def process_response(self, request, response):
        """Process responses for audit logging"""
        
        # Log certain actions automatically
        if request.user.is_authenticated and hasattr(request, 'start_time'):
            # Only log mutating operations and sensitive views
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                self.log_request(request, response)
        
        return response
    
    def update_session_activity(self, request):
        """Update user session activity"""
        if not request.session.session_key:
            return
        
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        parsed_ua = parse_user_agent(user_agent)
        
        # Update or create session
        UserSession.objects.update_or_create(
            session_key=request.session.session_key,
            defaults={
                'user': request.user,
                'ip_address': ip_address or '0.0.0.0',
                'user_agent': user_agent,
                'device_type': parsed_ua['device_type'],
                'browser': parsed_ua['browser'],
                'os': parsed_ua['os'],
                'last_activity': timezone.now(),
                'is_active': True,
            }
        )
    
    def log_request(self, request, response):
        """Log request to audit log"""
        settings = SystemSettings.get_settings()
        
        # Check if audit logging is enabled
        if not settings.enable_audit_logging:
            return
        
        # Skip logging for certain paths
        skip_paths = ['/static/', '/media/', '/realtime-metrics/', '/audit-logs/']
        if any(request.path.startswith(path) for path in skip_paths):
            return
        
        # Determine action type
        action_type = 'VIEW'
        if request.method == 'POST':
            action_type = 'CREATE'
        elif request.method in ['PUT', 'PATCH']:
            action_type = 'UPDATE'
        elif request.method == 'DELETE':
            action_type = 'DELETE'
        
        # Skip VIEW actions unless specifically enabled
        if action_type == 'VIEW' and not settings.log_view_actions:
            return
        
        # Determine severity
        severity = 'LOW'
        if request.method == 'DELETE':
            severity = 'HIGH'
        elif request.method in ['POST', 'PUT', 'PATCH']:
            severity = 'MEDIUM'
        
        # Create audit log
        try:
            AuditLog.objects.create(
                user=request.user,
                user_type=getattr(request.user, 'user_type', ''),
                username=request.user.username,
                action_type=action_type,
                action_description=f"{request.method} request to {request.path}",
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                request_path=get_request_path(request),
                request_method=request.method,
                severity=severity,
            )
        except Exception as e:
            # Silently fail - don't break the request
            pass


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Middleware to detect and prevent brute force attacks
    """
    
    def process_request(self, request):
        """Check for brute force patterns"""
        
        if not request.user.is_authenticated:
            ip_address = get_client_ip(request)
            if not ip_address:
                return None
            
            # Check failed login attempts
            from datetime import timedelta
            one_hour_ago = timezone.now() - timedelta(hours=1)
            
            failed_attempts = LoginAttempt.objects.filter(
                ip_address=ip_address,
                success=False,
                timestamp__gte=one_hour_ago
            ).count()
            
            settings = SystemSettings.get_settings()
            
            # If exceeded threshold, block IP and log security event
            if failed_attempts >= settings.max_login_attempts:
                # Block IP
                BlockedIP.objects.get_or_create(
                    ip_address=ip_address,
                    defaults={
                        'reason': 'BRUTE_FORCE',
                        'description': f'Blocked after {failed_attempts} failed login attempts',
                        'blocked_until': timezone.now() + timedelta(
                            minutes=settings.lockout_duration_minutes
                        ),
                        'is_active': True,
                    }
                )
                
                # Log security event
                log_security_event(
                    event_type='BRUTE_FORCE',
                    risk_level='HIGH',
                    description=f'Brute force attack detected from IP {ip_address}',
                    request=request,
                    details={
                        'failed_attempts': failed_attempts,
                        'time_window': '1 hour'
                    },
                    auto_block=False  # Already blocked above
                )
                
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    'Too many failed login attempts. Your IP has been temporarily blocked.'
                )
        
        return None


# Signal handlers for login tracking
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful login"""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    parsed_ua = parse_user_agent(user_agent)
    
    # Create login attempt record
    LoginAttempt.objects.create(
        username=user.username,
        user=user,
        success=True,
        ip_address=ip_address or '0.0.0.0',
        user_agent=user_agent,
    )
    
    # Create user session
    if request.session.session_key:
        UserSession.objects.create(
            user=user,
            session_key=request.session.session_key,
            ip_address=ip_address or '0.0.0.0',
            user_agent=user_agent,
            device_type=parsed_ua['device_type'],
            browser=parsed_ua['browser'],
            os=parsed_ua['os'],
            is_active=True,
        )
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        user_type=getattr(user, 'user_type', ''),
        username=user.username,
        action_type='LOGIN',
        action_description=f'User logged in successfully',
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request.path,
        severity='LOW',
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    if user and request:
        ip_address = get_client_ip(request)
        
        # Update session
        if request.session.session_key:
            UserSession.objects.filter(
                session_key=request.session.session_key
            ).update(
                is_active=False,
                logout_time=timezone.now()
            )
        
        # Create audit log
        AuditLog.objects.create(
            user=user,
            user_type=getattr(user, 'user_type', ''),
            username=user.username,
            action_type='LOGOUT',
            action_description=f'User logged out',
            ip_address=ip_address,
            user_agent=get_user_agent(request),
            request_path=request.path,
            severity='LOW',
        )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempt"""
    username = credentials.get('username', '')
    ip_address = get_client_ip(request)
    
    # Create login attempt record
    LoginAttempt.objects.create(
        username=username,
        user=None,
        success=False,
        failure_reason='Invalid credentials',
        ip_address=ip_address or '0.0.0.0',
        user_agent=get_user_agent(request),
    )
    
    # Check if this should trigger a security event
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    recent_failures = LoginAttempt.objects.filter(
        username=username,
        ip_address=ip_address,
        success=False,
        timestamp__gte=one_hour_ago
    ).count()
    
    # Log security event if multiple failures
    if recent_failures >= 3:
        log_security_event(
            event_type='BRUTE_FORCE',
            risk_level='MEDIUM' if recent_failures < 5 else 'HIGH',
            description=f'Multiple failed login attempts for user {username}',
            request=request,
            details={
                'username': username,
                'failed_attempts': recent_failures,
                'time_window': '1 hour'
            }
        )


# Model change tracking signals
def create_audit_log_for_model_change(sender, instance, created, **kwargs):
    """Generic function to log model changes"""
    
    # Skip logging for certain models to avoid recursion
    skip_models = ['AuditLog', 'SecurityEvent', 'LoginAttempt', 'UserSession']
    if sender.__name__ in skip_models:
        return
    
    # Get current user from thread local storage (set by middleware)
    from threading import current_thread
    request = getattr(current_thread(), 'request', None)
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return
    
    action_type = 'CREATE' if created else 'UPDATE'
    
    try:
        AuditLog.objects.create(
            user=request.user,
            user_type=getattr(request.user, 'user_type', ''),
            username=request.user.username,
            action_type=action_type,
            action_description=f"{action_type.title()} {sender.__name__}: {str(instance)}",
            model_name=sender.__name__,
            object_repr=str(instance)[:200],
            ip_address=get_client_ip(request) if request else None,
            severity='MEDIUM' if action_type == 'CREATE' else 'LOW',
        )
    except Exception:
        pass  # Silently fail


# Connect signals for important models
# You can add more models to track here
from django.apps import apps

def connect_audit_signals():
    """Connect audit signals for all models"""
    # Get important models to track
    models_to_track = [
        'Student', 'Lecturer', 'User', 'Programme', 'Unit',
        'UnitEnrollment', 'StudentMarks', 'FeePayment'
    ]
    
    for model_name in models_to_track:
        try:
            model = apps.get_model('main_application', model_name)  
            post_save.connect(create_audit_log_for_model_change, sender=model)
        except LookupError:
            pass  # Model not found, skip


# Middleware to add request to thread local
class ThreadLocalMiddleware(MiddlewareMixin):
    """Store request in thread local for access in signals"""
    
    def process_request(self, request):
        from threading import current_thread
        current_thread().request = request
        return None
    
    def process_response(self, request, response):
        from threading import current_thread
        if hasattr(current_thread(), 'request'):
            delattr(current_thread(), 'request')
        return response