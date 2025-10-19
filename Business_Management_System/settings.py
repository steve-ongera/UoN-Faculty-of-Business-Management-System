import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main_application',
]

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this for static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main_application.middleware.ThreadLocalMiddleware',
    'main_application.middleware.SecurityMiddleware',
    'main_application.middleware.BruteForceProtectionMiddleware',
    # Add chatbot middleware
    'main_application.middleware.ChatbotMiddleware',
    'main_application.middleware.ChatbotAnalyticsMiddleware',
    'main_application.middleware.ChatbotSecurityMiddleware',
    'main_application.middleware.ChatbotSessionMiddleware',
    'main_application.middleware.CrisisDetectionMiddleware',
]

ROOT_URLCONF = 'Business_Management_System.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main_application.context_processors.chatbot_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'Business_Management_System.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / config('DATABASE_NAME', default='db.sqlite3'),
    }
}

AUTH_USER_MODEL = 'main_application.User'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='Africa/Nairobi')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise configuration for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security Settings (for production)
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


# Chatbot settings
CHATBOT_SETTINGS = {
    # General settings
    'ENABLED': True,
    'MAX_MESSAGE_LENGTH': 2000,
    'SESSION_TIMEOUT_MINUTES': 60,
    
    # Rate limiting
    'RATE_LIMIT_MESSAGES_PER_HOUR': 100,
    'RATE_LIMIT_CONVERSATIONS_PER_HOUR': 20,
    
    # AI Model settings
    'AI_MODEL': 'gpt-4',
    'AI_TEMPERATURE': 0.7,
    'AI_MAX_TOKENS': 500,
    
    # Crisis detection
    'CRISIS_DETECTION_ENABLED': True,
    'CRISIS_AUTO_NOTIFY_STAFF': True,
    'CRISIS_NOTIFICATION_EMAILS': [
        'dean@university.ac.ke',
        'counselor@university.ac.ke',
    ],
    
    # Mental health
    'MENTAL_HEALTH_ASSESSMENTS_ENABLED': True,
    'HIGH_RISK_AUTO_REFERRAL': True,
    
    # Analytics
    'ANALYTICS_ENABLED': True,
    'TRACK_SENTIMENT': True,
    'TRACK_RESPONSE_TIME': True,
}

# Emergency contacts
EMERGENCY_CONTACTS = {
    'EMERGENCY_SERVICES': '999',
    'KENYA_RED_CROSS': '1199',
    'BEFRIENDERS_KENYA': '+254722178177',
    'CAMPUS_SECURITY': '+254XXXXXXXXX',
    'COUNSELING_CENTER': '+254XXXXXXXXX',
    'DEAN_OF_STUDENTS': '+254XXXXXXXXX',
}

# Mental health resources
MENTAL_HEALTH_RESOURCES = {
    'emergency': [
        {
            'name': 'Emergency Services',
            'number': '999',
            'available': '24/7',
            'description': 'For immediate emergencies'
        },
        {
            'name': 'Kenya Red Cross',
            'number': '1199',
            'available': '24/7',
            'description': 'Emergency support and crisis intervention'
        },
        {
            'name': 'Befrienders Kenya',
            'number': '+254722178177',
            'available': '24/7',
            'description': 'Emotional support and suicide prevention'
        },
    ],
    'campus': [
        {
            'name': 'University Counseling Center',
            'location': 'Main Administration Block, 2nd Floor',
            'available': '24/7',
            'email': 'counseling@university.ac.ke',
        },
        {
            'name': 'Dean of Students Office',
            'location': 'Student Affairs Building',
            'available': 'Mon-Fri 8AM-5PM',
            'email': 'dean.students@university.ac.ke',
        },
        {
            'name': 'Student Wellness Office',
            'location': 'Health Center',
            'available': 'Mon-Fri 9AM-5PM',
            'email': 'wellness@university.ac.ke',
        },
    ],
    'online': [
        {
            'name': 'Mental Health Kenya',
            'url': 'https://mentalhealthkenya.org',
            'description': 'Resources and information on mental health in Kenya'
        },
        {
            'name': 'KEMRI Wellcome Trust',
            'url': 'https://kemri-wellcome.org',
            'description': 'Mental health research and resources'
        },
    ]
}

# Chatbot knowledge base categories
CHATBOT_CATEGORIES = [
    'ACADEMIC',
    'MENTAL_HEALTH',
    'REGISTRATION',
    'FEES',
    'TIMETABLE',
    'GRADES',
    'CAREER',
    'GENERAL',
]

# Crisis keywords (case-insensitive)
CRISIS_KEYWORDS = {
    'CRITICAL': [
        'suicide', 'kill myself', 'end my life', 'want to die',
        'better off dead', 'end it all', 'no reason to live'
    ],
    'HIGH': [
        'self harm', 'hurt myself', 'cut myself', 'overdose',
        'harm myself', 'self-harm'
    ],
    'MEDIUM': [
        "can't go on", 'no point', 'give up', 'hopeless',
        'worthless', 'burden', 'pointless'
    ],
}

# Sentiment analysis keywords
SENTIMENT_KEYWORDS = {
    'POSITIVE': [
        'happy', 'great', 'excellent', 'good', 'thanks',
        'helpful', 'wonderful', 'fantastic', 'amazing'
    ],
    'NEGATIVE': [
        'sad', 'upset', 'angry', 'frustrated', 'disappointed',
        'terrible', 'awful', 'horrible', 'bad'
    ],
    'ANXIOUS': [
        'anxious', 'worried', 'stressed', 'panic', 'overwhelmed',
        'nervous', 'scared', 'afraid', 'terrified'
    ],
    'DEPRESSED': [
        'depressed', 'sad', 'hopeless', 'empty', 'numb',
        'worthless', 'lonely', 'isolated'
    ],
}

# Email configuration for alerts
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Update with your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@university.ac.ke'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@university.ac.ke'

# SMS configuration (for crisis alerts)
SMS_BACKEND = 'your_sms_provider'
SMS_API_KEY = 'your-api-key'
SMS_SENDER_ID = 'UNIVERSITY'

# Celery configuration (for async tasks)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'


# Cache configuration (for chatbot responses)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'chatbot',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True