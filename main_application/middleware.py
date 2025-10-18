"""
Optimized Security Middleware with SQLite lock handling
"""

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.db import transaction
from django.core.cache import cache
from .models import (
    AuditLog, SecurityEvent, LoginAttempt, UserSession, 
    BlockedIP, SystemSettings
)
from .utils import (
    get_client_ip, get_user_agent, get_request_path, 
    parse_user_agent, is_ip_blocked, log_security_event
)
import json
from datetime import timedelta


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to handle security features with optimized database access
    """
    
    def process_request(self, request):
        """Process incoming requests for security checks"""
        
        # Get client IP
        ip_address = get_client_ip(request)
        
        # Check if IP is blocked (use cache to reduce DB queries)
        if ip_address:
            cache_key = f'ip_blocked_{ip_address}'
            is_blocked_cached = cache.get(cache_key)
            
            if is_blocked_cached is None:
                is_blocked, blocked_ip = is_ip_blocked(ip_address)
                cache.set(cache_key, is_blocked, 300)  # Cache for 5 minutes
            else:
                is_blocked = is_blocked_cached
            
            if is_blocked:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    'Access denied. Your IP address has been blocked.'
                )
        
        # Check maintenance mode (cached to reduce DB queries)
        maintenance_mode = cache.get('maintenance_mode')
        if maintenance_mode is None:
            try:
                settings = SystemSettings.get_settings()
                maintenance_mode = settings.maintenance_mode
                cache.set('maintenance_mode', maintenance_mode, 60)  # Cache for 1 minute
            except:
                maintenance_mode = False
        
        if maintenance_mode:
            if request.user.is_authenticated:
                if not (request.user.is_superuser or 
                       getattr(request.user, 'user_type', '') == 'ICT_ADMIN'):
                    from django.shortcuts import render
                    return render(request, 'maintenance.html', {
                        'message': 'System is currently under maintenance.'
                    })
            else:
                if not request.path.startswith('/admin/') and request.path != '/login/':
                    from django.shortcuts import render
                    return render(request, 'maintenance.html', {
                        'message': 'System is currently under maintenance.'
                    })
        
        # Track session activity (OPTIMIZED - only every 30 seconds per user)
        if request.user.is_authenticated:
            self.update_session_activity_throttled(request)
        
        request.start_time = timezone.now()
        return None
    
    def update_session_activity_throttled(self, request):
        """
        Update session activity with throttling to prevent database locks
        Only updates once every 30 seconds per session
        """
        if not request.session.session_key:
            return
        
        # Use cache to throttle updates
        cache_key = f'session_update_{request.session.session_key}'
        last_update = cache.get(cache_key)
        
        now = timezone.now()
        
        # Only update if more than 30 seconds have passed
        if last_update is None or (now - last_update).seconds >= 30:
            try:
                ip_address = get_client_ip(request)
                user_agent = get_user_agent(request)
                parsed_ua = parse_user_agent(user_agent)
                
                # Use transaction to handle locks better
                with transaction.atomic():
                    session, created = UserSession.objects.select_for_update().get_or_create(
                        session_key=request.session.session_key,
                        defaults={
                            'user': request.user,
                            'ip_address': ip_address or '0.0.0.0',
                            'user_agent': user_agent,
                            'device_type': parsed_ua['device_type'],
                            'browser': parsed_ua['browser'],
                            'os': parsed_ua['os'],
                            'is_active': True,
                        }
                    )
                    
                    if not created:
                        # Only update if it exists
                        session.last_activity = now
                        session.is_active = True
                        session.save(update_fields=['last_activity', 'is_active'])
                
                # Update cache
                cache.set(cache_key, now, 60)  # Cache for 1 minute
                
            except Exception as e:
                # Silently fail - don't break the request
                pass
    
    def process_response(self, request, response):
        """Process responses for audit logging (throttled)"""
        
        # Only log important actions
        if request.user.is_authenticated and hasattr(request, 'start_time'):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                # Don't log on every request - use cache to throttle
                cache_key = f'audit_logged_{request.user.id}_{request.path}'
                if not cache.get(cache_key):
                    self.log_request_async(request, response)
                    cache.set(cache_key, True, 5)  # Only log same action every 5 seconds
        
        return response
    
    def log_request_async(self, request, response):
        """Log request to audit log (non-blocking)"""
        try:
            settings = SystemSettings.get_settings()
            
            if not settings.enable_audit_logging:
                return
            
            # Skip certain paths
            skip_paths = ['/static/', '/media/', '/realtime-metrics/', 
                         '/audit-logs/', '/login-activity-chart/', 
                         '/user-activity-chart/', '/security-events-chart/']
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
            
            # Skip VIEW actions unless enabled
            if action_type == 'VIEW' and not settings.log_view_actions:
                return
            
            # Determine severity
            severity = 'LOW'
            if request.method == 'DELETE':
                severity = 'HIGH'
            elif request.method in ['POST', 'PUT', 'PATCH']:
                severity = 'MEDIUM'
            
            # Create audit log in a transaction
            with transaction.atomic():
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
            # Silently fail
            pass


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Middleware to detect and prevent brute force attacks (cached)
    """
    
    def process_request(self, request):
        """Check for brute force patterns"""
        
        if not request.user.is_authenticated and request.path.endswith('/login/'):
            ip_address = get_client_ip(request)
            if not ip_address:
                return None
            
            # Use cache to reduce DB queries
            cache_key = f'failed_attempts_{ip_address}'
            failed_count = cache.get(cache_key)
            
            if failed_count is None:
                # Query database
                one_hour_ago = timezone.now() - timedelta(hours=1)
                failed_count = LoginAttempt.objects.filter(
                    ip_address=ip_address,
                    success=False,
                    timestamp__gte=one_hour_ago
                ).count()
                cache.set(cache_key, failed_count, 300)  # Cache for 5 minutes
            
            # Get settings
            max_attempts = cache.get('max_login_attempts')
            if max_attempts is None:
                try:
                    settings = SystemSettings.get_settings()
                    max_attempts = settings.max_login_attempts
                    cache.set('max_login_attempts', max_attempts, 300)
                except:
                    max_attempts = 5
            
            # Block if exceeded
            if failed_count >= max_attempts:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    'Too many failed login attempts. Please try again later.'
                )
        
        return None


# Signal handlers for login tracking
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful login"""
    try:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        parsed_ua = parse_user_agent(user_agent)
        
        # Create login attempt record
        with transaction.atomic():
            LoginAttempt.objects.create(
                username=user.username,
                user=user,
                success=True,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent,
            )
        
        # Clear failed attempts cache
        cache.delete(f'failed_attempts_{ip_address}')
        
        # Create user session (only if doesn't exist)
        if request.session.session_key:
            with transaction.atomic():
                UserSession.objects.get_or_create(
                    session_key=request.session.session_key,
                    defaults={
                        'user': user,
                        'ip_address': ip_address or '0.0.0.0',
                        'user_agent': user_agent,
                        'device_type': parsed_ua['device_type'],
                        'browser': parsed_ua['browser'],
                        'os': parsed_ua['os'],
                        'is_active': True,
                    }
                )
        
        # Create audit log
        with transaction.atomic():
            AuditLog.objects.create(
                user=user,
                user_type=getattr(user, 'user_type', ''),
                username=user.username,
                action_type='LOGIN',
                action_description='User logged in successfully',
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request.path if hasattr(request, 'path') else '/',
                severity='LOW',
            )
    except Exception as e:
        # Silently fail
        pass


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    try:
        if user and request:
            ip_address = get_client_ip(request)
            
            # Update session
            if request.session.session_key:
                with transaction.atomic():
                    UserSession.objects.filter(
                        session_key=request.session.session_key
                    ).update(
                        is_active=False,
                        logout_time=timezone.now()
                    )
            
            # Create audit log
            with transaction.atomic():
                AuditLog.objects.create(
                    user=user,
                    user_type=getattr(user, 'user_type', ''),
                    username=user.username,
                    action_type='LOGOUT',
                    action_description='User logged out',
                    ip_address=ip_address,
                    user_agent=get_user_agent(request),
                    request_path=request.path if hasattr(request, 'path') else '/',
                    severity='LOW',
                )
    except Exception as e:
        pass


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempt"""
    try:
        username = credentials.get('username', '')
        ip_address = get_client_ip(request)
        
        # Create login attempt record
        with transaction.atomic():
            LoginAttempt.objects.create(
                username=username,
                user=None,
                success=False,
                failure_reason='Invalid credentials',
                ip_address=ip_address or '0.0.0.0',
                user_agent=get_user_agent(request),
            )
        
        # Increment cache counter
        cache_key = f'failed_attempts_{ip_address}'
        failed_count = cache.get(cache_key, 0)
        cache.set(cache_key, failed_count + 1, 3600)  # Cache for 1 hour
        
        # Log security event if multiple failures
        if failed_count >= 3:
            with transaction.atomic():
                log_security_event(
                    event_type='BRUTE_FORCE',
                    risk_level='MEDIUM' if failed_count < 5 else 'HIGH',
                    description=f'Multiple failed login attempts for user {username}',
                    request=request,
                    details={
                        'username': username,
                        'failed_attempts': failed_count,
                    }
                )
    except Exception as e:
        pass


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