"""
URL configuration for turnitin_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from django.views.generic import RedirectView
from .view import home_view, upload_file, get_web_user_assignments\
    ,delete_job, download_file


urlpatterns = [
    path('admin/', admin.site.urls),
    path('turnitingood/', include('api.urls')),  # 包含 api 模块的 URL
    path('', home_view, name='home'),  # 匿名用户主页
    path('<str:user_id>/', home_view, name='home_with_user'),  # 指定用户 ID 的主页
    path('turnitingood/upload/', upload_file, name='upload_file'),
    path('turnitingood/assignments/', get_web_user_assignments, name='get_web_user_assignments'),
    path('turnitingood/job/delete/', delete_job, name='delete_job'),
    path('turnitingood/job/download/', download_file, name='download_file'),


]



