import os
from pathlib import Path
import pymysql

pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = ''
DEBUG = False
ALLOWED_HOSTS = ['example.com', 'localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = [
    'https://example.com',
    'https://www.example.com',
    'http://localhost:8000',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_q',
    'api.apps.ApiConfig',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'turnitin_admin.middleware.exception_handler.GlobalExceptionMiddleware',
]

ROOT_URLCONF = 'turnitin_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [os.path.join(BASE_DIR, 'templates/jinja2')],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'turnitin_admin.jinja2_env.environment',
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',  # 降低日志级别以捕获更多信息
            'class': 'logging.FileHandler',
            'filename': 'django_errors.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'turnitin_admin': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

WSGI_APPLICATION = 'turnitin_admin.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'turniting',
        'USER': 'root' if DEBUG else 'turnitin',
        'PASSWORD': '' if DEBUG else '',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET time_zone='+08:00'"
        }
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'
USE_I18N = True

STATIC_ROOT = '/root/turniting_admin/static/'
STATIC_URL = '/static/'

# Update MEDIA_ROOT to an absolute path
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'media')) if DEBUG else '/root/turniting_admin/media/'
MEDIA_URL = '/media/'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 修改默认Admin配置
from django.contrib.admin import AdminSite
AdminSite.site_header = "Turnitin 管理系统"
AdminSite.site_title = "管理后台"
AdminSite.index_title = "仪表盘"



# 配置 django-q 使用数据库后端（无需 Redis）
Q_CLUSTER = {
    'name': 'myproject',
    'workers': 3,  # 最大并发工作进程数
    'recycle': 50,  # 每个worker处理500个任务后重启（防内存泄漏）
    'timeout': 60,  # 任务超时时间（秒）
    'compress': True,  # 压缩任务数据
    'save_limit': 0,  # 历史任务保留数量
    'queue_limit': 0,  # 队列最大积压任务数
    'redis': {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0, 
    },
    'retry': 0
}

# 时区设置
TIME_ZONE = 'Asia/Shanghai'  # 匹配 HKT
USE_TZ = False

REDIS_HOST = 'localhost'  
REDIS_PORT = 6379       
