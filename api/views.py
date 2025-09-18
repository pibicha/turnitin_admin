from django.shortcuts import render

from rest_framework import viewsets
from .models import AlertMessage, TurnitinAccount, TurnitinClass,\
    User, Assignment,UserAssignment,PackageConfig,RechargeRecord,\
    WebUser, WebAssignments, WebUserAssignments,WebTurnitinClass
    
from .serializers import AlertMessageSerializer, \
TurnitinAccountSerializer, TurnitinClassSerializer,\
UserSerializer, AssignmentSerializer,UserAssignmentSerializer,\
PackageConfigSerializer, RechargeRecordSerializer,\
WebUserSerializer, WebAssignmentsSerializer, WebUserAssignmentsSerializer,\
WebTurnitinClassSerializer



class AlertMessageViewSet(viewsets.ModelViewSet):
    queryset = AlertMessage.objects.all()
    serializer_class = AlertMessageSerializer


class TurnitinAccountViewSet(viewsets.ModelViewSet):
    queryset = TurnitinAccount.objects.all()
    serializer_class = TurnitinAccountSerializer
    

class TurnitinClassViewSet(viewsets.ModelViewSet):
    queryset = TurnitinClass.objects.all()
    serializer_class = TurnitinClassSerializer
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    
class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    
class UserAssignmentViewSet(viewsets.ModelViewSet):
    queryset = UserAssignment.objects.all()
    serializer_class = UserAssignmentSerializer
    
class PackageConfigViewSet(viewsets.ModelViewSet):
    queryset = PackageConfig.objects.all()
    serializer_class = PackageConfigSerializer
    
class RechargeRecordViewSet(viewsets.ModelViewSet):
    queryset = RechargeRecord.objects.all()
    serializer_class = RechargeRecordSerializer
    
class WebUserViewSet(viewsets.ModelViewSet):
    queryset = WebUser.objects.all()
    serializer_class = WebUserSerializer

class WebAssignmentsViewSet(viewsets.ModelViewSet):
    queryset = WebAssignments.objects.all()
    serializer_class = WebAssignmentsSerializer

class WebUserAssignmentsViewSet(viewsets.ModelViewSet):
    queryset = WebUserAssignments.objects.all()
    serializer_class = WebUserAssignmentsSerializer
   
class WebTurnitinClassViewSet(viewsets.ModelViewSet):
    queryset = WebTurnitinClass.objects.all()
    serializer_class = WebTurnitinClassSerializer 
    
    