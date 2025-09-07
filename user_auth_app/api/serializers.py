from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .auth_utils import validate_password_match, remove_password2_from_data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password confirmation"""
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, attrs):
        """Validates registration data"""
        password = attrs['password']
        password2 = attrs['password2']
        validate_password_match(password, password2)
        return attrs
    
    def create(self, validated_data):
        """Creates new user"""
        validated_data = remove_password2_from_data(validated_data)
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']