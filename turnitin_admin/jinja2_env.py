# turnitin_admin/jinja2_env.py
from django.middleware.csrf import get_token
import jinja2

def environment(**options):
    env = jinja2.Environment(**options)
    
    # 添加 CSRF 相关全局函数
    env.globals.update({
        'get_csrf_token': get_token,  # 直接传递 Django 的 get_token 函数
        'csrf_input': lambda request: (
            f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'
        )
    })
    
    return env