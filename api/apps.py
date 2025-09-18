from django.apps import AppConfig
import os
import sys

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    def ready(self):
        # 仅在主进程中启动，避免多进程重复
        if os.environ.get('RUN_MAIN', None) != 'true' or 'pytest' in sys.argv[0]:
            return
