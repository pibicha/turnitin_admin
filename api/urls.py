from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertMessageViewSet, TurnitinAccountViewSet,\
    TurnitinClassViewSet, UserViewSet, AssignmentViewSet,UserAssignmentViewSet,\
    PackageConfigViewSet,RechargeRecordViewSet,\
    WebUserViewSet, WebAssignmentsViewSet, WebUserAssignmentsViewSet,\
    WebTurnitinClassViewSet
    
router = DefaultRouter()
router.register(r'alert_message', AlertMessageViewSet)
router.register(r'turntin_account', TurnitinAccountViewSet)
router.register(r'turntin_class', TurnitinClassViewSet)
router.register(r'wechat_user', UserViewSet)
router.register(r'assignment', AssignmentViewSet)
router.register(r'user_assignment', UserAssignmentViewSet)
router.register(r'package_config', PackageConfigViewSet)
router.register(r'recharge_record', RechargeRecordViewSet)

# Web router for web-related endpoints
web_router = DefaultRouter()
web_router.register(r'web_user', WebUserViewSet)
web_router.register(r'web_assignments', WebAssignmentsViewSet)
web_router.register(r'web_user_assignments', WebUserAssignmentsViewSet)
web_router.register(r'web_turnitin_class', WebTurnitinClassViewSet)



urlpatterns = [
    path('', include(router.urls)),
    path('web/', include(web_router.urls)),
]