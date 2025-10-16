def get_client_ip(request):
    """
    Get the client's IP address from the request.
    Handles proxies and load balancers by checking multiple headers.
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        str: Client IP address or None if not found
    """
    # List of headers to check in order of preference
    ip_headers = [
        'HTTP_X_FORWARDED_FOR',  # Standard proxy header
        'HTTP_X_REAL_IP',         # Nginx proxy header
        'HTTP_CF_CONNECTING_IP',  # Cloudflare
        'HTTP_X_CLUSTER_CLIENT_IP',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
        'REMOTE_ADDR',            # Direct connection
    ]
    
    for header in ip_headers:
        ip = request.META.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
            # The first IP is the original client
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            
            # Remove port if present
            if ':' in ip and '.' in ip:  # IPv4 with port
                ip = ip.split(':')[0]
            
            # Basic validation
            if ip and ip != '':
                return ip
    
    # Fallback to None if no IP found
    return None


def get_user_agent(request):
    """
    Get the user agent string from the request.
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        str: User agent string or empty string if not found
    """
    return request.META.get('HTTP_USER_AGENT', '')


def get_request_path(request):
    """
    Get the full request path including query string.
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        str: Full request path
    """
    path = request.path
    if request.META.get('QUERY_STRING'):
        path += '?' + request.META.get('QUERY_STRING')
    return path


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract device type, browser, and OS.
    This is a simple parser - for production use, consider using a library like user-agents.
    
    Args:
        user_agent_string: User agent string
    
    Returns:
        dict: Dictionary containing device_type, browser, and os
    """
    user_agent_string = user_agent_string.lower()
    
    # Determine device type
    device_type = 'Desktop'
    if 'mobile' in user_agent_string or 'android' in user_agent_string:
        device_type = 'Mobile'
    elif 'tablet' in user_agent_string or 'ipad' in user_agent_string:
        device_type = 'Tablet'
    
    # Determine browser
    browser = 'Unknown'
    if 'edg' in user_agent_string:
        browser = 'Microsoft Edge'
    elif 'chrome' in user_agent_string and 'edg' not in user_agent_string:
        browser = 'Chrome'
    elif 'firefox' in user_agent_string:
        browser = 'Firefox'
    elif 'safari' in user_agent_string and 'chrome' not in user_agent_string:
        browser = 'Safari'
    elif 'opera' in user_agent_string or 'opr' in user_agent_string:
        browser = 'Opera'
    elif 'msie' in user_agent_string or 'trident' in user_agent_string:
        browser = 'Internet Explorer'
    
    # Determine OS
    os = 'Unknown'
    if 'windows' in user_agent_string:
        os = 'Windows'
    elif 'mac os' in user_agent_string or 'macos' in user_agent_string:
        os = 'macOS'
    elif 'linux' in user_agent_string:
        os = 'Linux'
    elif 'android' in user_agent_string:
        os = 'Android'
    elif 'ios' in user_agent_string or 'iphone' in user_agent_string or 'ipad' in user_agent_string:
        os = 'iOS'
    
    return {
        'device_type': device_type,
        'browser': browser,
        'os': os
    }


def log_audit_action(user, action_type, description, model_name='', object_repr='', 
                     old_values=None, new_values=None, severity='LOW', request=None):
    """
    Helper function to create audit log entries.
    
    Args:
        user: User object performing the action
        action_type: Type of action (CREATE, UPDATE, DELETE, etc.)
        description: Human-readable description
        model_name: Name of the model affected
        object_repr: String representation of the object
        old_values: Previous values (dict)
        new_values: New values (dict)
        severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        request: Django HttpRequest object (optional)
    
    Returns:
        AuditLog: Created audit log instance
    """
    from .models import AuditLog
    
    log_data = {
        'user': user,
        'user_type': getattr(user, 'user_type', ''),
        'username': user.username,
        'action_type': action_type,
        'action_description': description,
        'model_name': model_name,
        'object_repr': object_repr,
        'old_values': old_values,
        'new_values': new_values,
        'severity': severity,
    }
    
    if request:
        log_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': get_user_agent(request),
            'request_path': get_request_path(request),
            'request_method': request.method,
        })
    
    return AuditLog.objects.create(**log_data)


def log_security_event(event_type, risk_level, description, user=None, 
                       request=None, details=None, auto_block=False):
    """
    Helper function to create security event entries.
    
    Args:
        event_type: Type of security event
        risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        description: Human-readable description
        user: User object (optional)
        request: Django HttpRequest object (optional)
        details: Additional details (dict)
        auto_block: Whether to auto-block the IP
    
    Returns:
        SecurityEvent: Created security event instance
    """
    from .models import SecurityEvent, BlockedIP
    from django.utils import timezone
    
    event_data = {
        'event_type': event_type,
        'risk_level': risk_level,
        'description': description,
        'details': details,
        'auto_blocked': auto_block,
    }
    
    if user:
        event_data.update({
            'user': user,
            'username': user.username,
        })
    
    if request:
        ip_address = get_client_ip(request)
        event_data.update({
            'ip_address': ip_address,
            'user_agent': get_user_agent(request),
            'request_path': get_request_path(request),
        })
        
        # Auto-block if enabled
        if auto_block and ip_address:
            BlockedIP.objects.get_or_create(
                ip_address=ip_address,
                defaults={
                    'reason': 'AUTOMATED_BLOCK',
                    'description': f'Auto-blocked due to {event_type}',
                    'blocked_until': timezone.now() + timezone.timedelta(hours=24),
                }
            )
    
    return SecurityEvent.objects.create(**event_data)


def log_login_attempt(username, success, request, failure_reason='', user=None):
    """
    Helper function to log login attempts.
    
    Args:
        username: Username attempting to login
        success: Whether login was successful
        request: Django HttpRequest object
        failure_reason: Reason for failure (if applicable)
        user: User object (if successful)
    
    Returns:
        LoginAttempt: Created login attempt instance
    """
    from .models import LoginAttempt
    
    return LoginAttempt.objects.create(
        username=username,
        user=user,
        success=success,
        failure_reason=failure_reason,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


def is_ip_blocked(ip_address):
    """
    Check if an IP address is currently blocked.
    
    Args:
        ip_address: IP address to check
    
    Returns:
        tuple: (is_blocked, blocked_ip_object or None)
    """
    from .models import BlockedIP
    from django.utils import timezone
    
    try:
        blocked_ip = BlockedIP.objects.get(ip_address=ip_address, is_active=True)
        
        # Check if block has expired
        if blocked_ip.blocked_until and timezone.now() >= blocked_ip.blocked_until:
            blocked_ip.is_active = False
            blocked_ip.save()
            return False, None
        
        return True, blocked_ip
    except BlockedIP.DoesNotExist:
        return False, None


def check_failed_login_threshold(username, ip_address, max_attempts=5):
    """
    Check if failed login attempts exceed threshold.
    
    Args:
        username: Username attempting login
        ip_address: IP address of the attempt
        max_attempts: Maximum allowed attempts
    
    Returns:
        tuple: (should_block, attempt_count)
    """
    from .models import LoginAttempt
    from django.utils import timezone
    
    # Check failed attempts in the last hour
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    
    failed_attempts = LoginAttempt.objects.filter(
        username=username,
        ip_address=ip_address,
        success=False,
        timestamp__gte=one_hour_ago
    ).count()
    
    return failed_attempts >= max_attempts, failed_attempts