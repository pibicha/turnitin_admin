from rest_framework import serializers
from .models import AlertMessage, TurnitinAccount, \
    User, TurnitinClass,Assignment,UserAssignment,\
    PackageConfig,RechargeRecord,\
    WebUser, WebAssignments, WebUserAssignments, WebTurnitinClass

class AlertMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertMessage
        fields = '__all__'


class TurnitinAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurnitinAccount
        fields = '__all__'
        
        
class TurnitinClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TurnitinClass
        fields = '__all__'
        
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        
class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = '__all__'
        
class UserAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAssignment
        fields = '__all__'
        
class PackageConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageConfig
        fields = '__all__'
        

class RechargeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RechargeRecord
        fields = '__all__'
        
class WebUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebUser
        fields = '__all__'

class WebAssignmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebAssignments
        fields = '__all__'

class WebUserAssignmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebUserAssignments
        fields = '__all__'
        
        

class WebTurnitinClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebTurnitinClass
        fields = '__all__'